import uuid

import requests
import random
import string

from utils.logger import logger
from utils.sqli_payloads import SQLI_BASIC, SQL_ERRORS
from utils.severity import SQLI_SEVERITY, SEVERITY_NAMES, VULNERABILITY_INFO
from models.vulnerability import Vulnerability

from urllib.parse import quote

import re

class JuiceShopSQLi:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                     'Content-Type': 'application/json'})
        self.result = []
        self.auth_token = None

    def register_user(self, email, password):
        """Регистрация пользователя"""
        url = f"{self.base_url}/api/Users"
        data = {
            "email": email,
            "password": password,
            "passwordRepeat": password,
            "securityQuestion": 1,
            "securityAnswer": "test"
        }
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 201:
                logger.debug(f"User registered {email}")
                return True
            else:
                logger.error(f"Failed registration{email} status code {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка регистрации {email}: {e}")
            return False

    def login(self, email, password):
        """Логин и получения токена авторизации"""
        url = f"{self.base_url}/rest/user/login"
        data = {"email": email, "password": password}
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                token = response.json().get("authentication", {}).get("token")
                if token:
                    self.auth_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    logger.debug(f"Logged in as {email}")
                    return True
        except Exception as e:
            logger.error(f"Failed login {email}: {e}")
        return False

    def test_sqli_fields(self,
                         url: str,
                         method: str,
                         base_data: dict,
                         fields: list[str]):
        """
        Универсальное тестирование SQLi
        :param url: URL эндпоинт
        :param method: GET - POST
        :param base_data: базовые данные запроса
        :param fields: список полей для инъекции
        :return:
        """

        # --- Снимаем baseline один раз для поля, до перебора payload'ов ---
        clean_data = base_data() if callable(base_data) else base_data.copy()
        baseline = self.get_baseline(url, method, clean_data)

        for field in fields:
            for payload in SQLI_BASIC:
                if callable(base_data):
                    data = base_data()
                else:
                    data = base_data.copy()

                data[field] = payload

                try:
                    if method.upper() == "GET":
                        response = self.session.get(url, params=data)
                    elif method.upper() == "POST":
                        response = self.session.post(url, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method {method}")

                    vulnerable, vuln_type, reason = self.detect_sqli(response, payload, baseline)

                    if vulnerable:
                        self.report_vulnerability(
                            vuln_type=vuln_type,
                            url=url,
                            parameter=field,
                            payload=payload,
                            reason=reason,
                            evidence=self.format_evidence(baseline, response)
                        )
                except Exception as e:
                    logger.error(f"SQLi test failed ( {url}, field={method}): {e}")

    def test_sqli_path_param(self, url_template: str, param_name: str, baseline_value: str):
        """
        Универсальное тестирование SQLi в path-параметре
        :param url_template: URL с плейсхолдером {value}, например: f"{self.base_url}/rest/track-order/{{value}}"
        :param param_name: имя параметра для отчёта (например "orderId)"
        :param baseline_value: валидное значение (например 1)
        """

        # --- Baseline: honest "чистый" запрос с валидным ID ---
        baseline_url = url_template.format(value=baseline_value)
        baseline = None

        try:
            baseline_response = self.session.get(baseline_url)
            baseline = self.analyze_response(baseline_response, payload=None, baseline=None)
        except Exception as e:
            logger.error(f"Baseline request failed ( {baseline_url}): {e}")

        # --- Перебор payloads ---
        for payload in SQLI_BASIC:
            try:
                # URL-кодируем payload, чтобы спецсимволы (', ", #, --) корректно ушли в path
                encode_payload = quote(payload, safe="")

                url = url_template.format(value=encode_payload)
                response = self.session.get(url)

                vulnerable, vuln_type, reason = self.detect_sqli(response, payload, baseline)

                if vulnerable:
                    self.report_vulnerability(
                        vuln_type=vuln_type,
                        url=url_template,
                        parameter=param_name,
                        payload=payload,
                        reason=reason,
                        evidence=self.format_evidence(baseline, response)
                    )
            except Exception as e:
                logger.error(f"SQLi path-param test failed ({url_template}, param={param_name}): {e}")

    def get_registration_template(self):

        suffix = uuid.uuid4().hex[:8]

        return {
            "email": f"scan_{suffix}@test.com",
            "password": "Password123",
            "passwordRepeat": "Password123",
            "securityQuestion": 1,
            "securityAnswer": "test"
        }

    def get_feedback_template(self):
        """
        Получить валидный шаблон Feedback
        """

        response = self.session.get(f"{self.base_url}/rest/captcha")
        response.raise_for_status()

        captcha = response.json()

        return {
            "captchaId": captcha["captchaId"],
            "captcha": captcha["answer"],
            "comment": "Test",
            "rating": 5
        }

    def get_address_template(self):
        """
        Шаблон создания адреса
        """
        return {
            "city": "TestCity",
            "country": "TestCountry",
            "fullName": "TestFullName",
            "mobileNum": 123456789,
            "state": "TestState",
            "streetAddress": "TestStreetAddress 1",
            "zipCode": "12345",
        }

    def get_card_template(self):
        """Шаблон создания карты"""
        return {
            "fullName": "Test User",
            "cardNum": 4111111111111111,
            "expMonth": 12,
            "expYear": 2099,
        }

    def get_recycle_template(self):
        """Шаблон заявки на утилизацию"""
        return {
            "quantity": "1",
            "AddressId": 1,
            "isPickup": True,
        }

    def report_vulnerability(self, vuln_type, url, parameter, payload, reason, evidence=None):
        """
        Регистрация найденной уязвимости
        """
        """
            Регистрация найденной уязвимости.
            """

        severity = SQLI_SEVERITY.get(vuln_type, 0)
        severity_name = SEVERITY_NAMES.get(severity, "Unknown")

        info = VULNERABILITY_INFO.get(vuln_type, {})

        scanner = info.get("scanner", "Unknown")
        cwe = info.get("cwe", "Unknown")

        vulnerability = Vulnerability(
            scanner=scanner,
            vuln_type=vuln_type,
            severity=severity,
            severity_name=severity_name,
            url=url,
            parameter=parameter,
            payload=payload,
            reason=reason,
            confidence="High",
            evidence=evidence,
            cwe=cwe
        )

        signature = (
            vulnerability.vuln_type,
            vulnerability.url,
            vulnerability.parameter,
            vulnerability.payload
        )

        if not hasattr(self, "_reported"):
            self._reported = set()

        if signature in self._reported:
            return

        self._reported.add(signature)

        self.result.append(vulnerability)

        logger.warning(
            f"\n[{vulnerability.severity_name}] {vulnerability.vuln_type}"
            f"\nScanner   : {vulnerability.scanner}"
            f"\nCWE       : {vulnerability.cwe}"
            f"\nURL       : {vulnerability.url}"
            f"\nParameter : {vulnerability.parameter}"
            f"\nPayload   : {vulnerability.payload}"
            f"\nReason    : {vulnerability.reason}"
            + (
                f"\nEvidence  : {vulnerability.evidence}"
                if vulnerability.evidence else ""
            )
            + "\n" + "-" * 60
        )

    def format_evidence(self, baseline, response):
        """
        Формирует evidence-строку со сравнением baseline vs текущей строкой.
        """
        if not baseline:
            return None

        current_time = response.elapsed.total_seconds()
        current_size = len(response.content)

        parts = [
            f"baseline_time={baseline.get('response_time', 0):.2f}",
            f"current_time={current_time:.2f}s",
            f"baseline_size={baseline.get('response_size', 0)}b",
            f"current_size={current_size}b",
        ]

        if baseline.get("record_count") is not None:
            parts.append(f"baseline_records={baseline['record_count']}")

        return ", ".join(parts)

    def analyze_response(self, response, payload=None, baseline=None):
        """
        Анализ HTTP-ответа и поиск признаков SQL-инъекции.
        В дальнейшем используется и другими сканерами.
        """

        text = response.text
        text_lower = text.lower()

        analysis = {
            # Общая информация
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", "").lower(),

            # Признаки уязвимости
            "sql_error": False,
            "server_error": False,
            "auth_bypass": False,
            "large_result": False,
            "payload_reflected": False,
            "time_based": False,
            "record_count_diff": None,

            # Дополнительная информация
            "dbms": None,
            "is_json": False,

            # Метрики
            "response_size": len(response.content),
            "response_time": response.elapsed.total_seconds(),
            "record_count": None,
        }

        # --------------------------------------------------
        # Проверка отражения payload
        # --------------------------------------------------

        search_text = text_lower

        if payload:
            payload_lower = payload.lower()

            if payload_lower in text_lower:
                analysis["payload_reflected"] = True

                # Исключаем payload из дальнейшего анализа,
                # чтобы избежать ложных срабатываний
                search_text = search_text.replace(payload_lower, "")

        # --------------------------------------------------
        # Поиск сообщений SQL
        # --------------------------------------------------

        for dbms, patterns in SQL_ERRORS.items():
            for pattern in patterns:

                if re.search(pattern, search_text, re.IGNORECASE):
                    analysis["sql_error"] = True
                    analysis["dbms"] = dbms
                    break

            if analysis["sql_error"]:
                break

        # --------------------------------------------------
        # Ошибка сервера
        # --------------------------------------------------

        if response.status_code >= 500:
            analysis["server_error"] = True

        # --------------------------------------------------
        # Проверка обхода авторизации
        # --------------------------------------------------

        if (
                response.status_code == 200
                and "authentication" in text_lower
                and "token" in text_lower
        ):
            analysis["auth_bypass"] = True

        # --------------------------------------------------
        # Анализ JSON
        # --------------------------------------------------

        try:
            json_data = response.json()
            analysis["is_json"] = True

            if isinstance(json_data, dict):
                data = json_data.get("data")

                if isinstance(data, list) and len(data) > 20:
                    analysis["record_count"] = len(data)

        except ValueError:
            pass

        # --------------------------------------------------
        # Сравнение с baseline
        # --------------------------------------------------

        if baseline:
            # Large result: сравниваем не с фиксированным числом, а с baseline
            if (
                analysis["record_count"] is not None
                and baseline.get("record_count") is not None
            ):
                base_count = baseline["record_count"]
                cur_count = analysis["record_count"]

                # флагуем, если данных стало заметно больше
                if cur_count > base_count + 5 and (
                    base_count == 0 or cur_count > base_count * 1.5
                ):
                    analysis["large_result"] = True

            # Time based blind: сравниваем время ответа с baseline
            base_time = baseline.get("response_time", 0)
            cur_time = analysis["response_time"]

            # Порог: минимум 4 сек. разницы, чтобы не ловить джиттер сети
            if cur_time - base_time >= 4.0:
                analysis["time_based"] = True

        return analysis

    def get_baseline(self, url, method, data):
        """
        Делает "чистый" запрос без SQLi и возвращает его анализ.
        Используется как точка отсчёта для сравнения.
        """
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=data)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return self.analyze_response(response, payload=None, baseline=None)

        except Exception as e:
            logger.error(f"Baseline request failed: ({url}): {e}")
            return None

    def detect_sqli(self, response, payload=None, baseline=None):
        """
        Определяет признаки SQLi
        """

        analysis = self.analyze_response(response, payload, baseline)

        # Самый сильный признак
        if analysis["auth_bypass"]:
            return (
                True,
                "SQLi_Auth",
                "Authentication bypass"
            )

        elif analysis["time_based"]:
            delay = analysis["response_time"] - (baseline.get("response_time", 0) if baseline else 0)
            return (
                True,
                "SQLi_Blind_Time",
                f"Response delayed by {delay:.2f} vs baseline time"

            )

        # Изменилось кол-во данных
        elif analysis["large_result"]:
            return (
                True,
                "SQLi_Data",
                "Abnormally large result set"
            )

        # Сообщение БД
        elif analysis["sql_error"]:
            return (
                True,
                "SQLi_Error",
                f"Database error ({analysis['dbms']})"
            )

        return (
            False,
            None,
            None
        )

    def test_sqli_search(self):

        self.test_sqli_fields(
            url=f"{self.base_url}/rest/products/search",
            method="GET",
            base_data={"q": "zzznonexistentproduct9999"},
            fields=["q"]
        )

    def test_sqli_login(self):
        """SQLi на форме входа (инъекция в email)"""
        self.test_sqli_fields(
            url=f"{self.base_url}/rest/user/login",
            method="POST",
            base_data={"email": "scan@test.com", "password": "password"},
            fields=["email", "password"]
        )

    def test_sqli_registration(self):
        """
        Проверка SQLi при регистрации пользователя
        """
        self.test_sqli_fields(
            url=f"{self.base_url}/api/Users",
            method="POST",
            base_data=self.get_registration_template,
            fields=["email", "password", "securityAnswer"]
        )

    def test_sqli_feedbacks(self):
        """
        Проверка SQLi в Feedback API
        """
        self.test_sqli_fields(
            url=f"{self.base_url}/api/Feedbacks",
            method="POST",
            base_data=self.get_feedback_template,
            fields=["comment", "rating"]
        )

    def test_sqli_address(self):
        """
        Проверка SQLi в Address API
        """
        rand_suffix = ''.join(
            random.choices(string.ascii_lowercase, k=6)
        )

        email = f"test_{rand_suffix}@test.com"
        password = "Password123"

        if not self.register_user(email, password):
            logger.error(f"Registration failed")
            return

        if not self.auth_token:
            if not self.login(email, password):
                logger.error(f"Authentication failed")
                return
        self.test_sqli_fields(
            url=f"{self.base_url}/api/Addresss",
            method="POST",
            base_data=self.get_address_template,
            fields=[
                "city",
                "country",
                "fullName",
                "mobileNum",
                "state",
                "streetAddress",
                "zipCode"
            ]
        )

    def test_sqli_card(self):
        """Проверка SQLi в Card API"""
        rand_suffix = ''.join(
            random.choices(string.ascii_lowercase, k=6)
        )
        email = f"test_{rand_suffix}@test.com"
        password = "Password123"

        if not self.register_user(email, password):
            logger.error(f"Registration failed")
            return
        if not self.auth_token:
            if not self.login(email, password):
                logger.error(f"Authentication failed")
                return

        self.test_sqli_fields(
            url=f"{self.base_url}/api/Cards",
            method="POST",
            base_data=self.get_card_template,
            fields=["fullName", "cardNum"]
        )

    def test_sqli_recycle(self):
        """Проверка SQLi Recycle API"""
        rand_suffix = ''.join(
            random.choices(string.ascii_lowercase, k=6)
        )
        email = f"test_{rand_suffix}@test.com"
        password = "Password123"

        if not self.register_user(email, password):
            logger.error(f"Registration failed")
            return
        if not self.auth_token:
            if not self.login(email, password):
                logger.error(f"Authentication failed")
                return

        self.test_sqli_fields(
            url=f"{self.base_url}/api/Recycles",
            method="POST",
            base_data=self.get_recycle_template,
            fields=["quantity", "AddressId"]
        )

    def test_sqli_track_order(self):
        """
        Проверка SQLi в path-параметре /rest/track-order/{id}
        """
        self.test_sqli_path_param(
            url_template=f"{self.base_url}/rest/track-order/{{value}}",
            param_name="orderId",
            baseline_value="1"
        )

    def test_sqli_product_by_id(self):
        """
        Проверка SQLi в path-параметре /api/Products/{id}
        """
        self.test_sqli_path_param(
            url_template=f"{self.base_url}/api/Products/{{value}}",
            param_name="id",
            baseline_value="1"
        )

    def print_summary(self):
        """
        Вывод итогового отчёта по найденным уязвимостям.
        """

        logger.info("=" * 70)
        logger.info("                ОТЧЁТ СКАНЕРА УЯЗВИМОСТЕЙ")
        logger.info("=" * 70)

        if not self.result:
            logger.info("Уязвимостей не найдено.")
            logger.info("=" * 70)
            return

        logger.info(f"Всего найдено: {len(self.result)}")
        logger.info("")

        # Сортировка по критичности
        sorted_result = sorted(
            self.result,
            key=lambda vuln: vuln.severity,
            reverse=True
        )

        for vuln in sorted_result:

            logger.warning(f"[{vuln.severity_name}] {vuln.vuln_type}")
            logger.warning(f"URL        : {vuln.url}")
            logger.warning(f"Parameter  : {vuln.parameter}")
            logger.warning(f"Payload    : {vuln.payload}")
            logger.warning(f"Reason     : {vuln.reason}")

            if vuln.confidence:
                logger.warning(f"Confidence : {vuln.confidence}")

            if vuln.cwe:
                logger.warning(f"CWE        : {vuln.cwe}")

            if vuln.evidence:
                logger.warning(f"Evidence   : {vuln.evidence}")

            logger.warning("-" * 70)

        logger.info("=" * 70)

    def run_all_tests(self):
        logger.info("=== Running SQLi testing ===")
        self.test_sqli_search()
        self.test_sqli_login()
        self.test_sqli_registration()
        self.test_sqli_feedbacks()
        self.test_sqli_address()
        self.test_sqli_track_order()
        self.test_sqli_product_by_id()
        self.test_sqli_card()
        self.test_sqli_recycle()
        self.print_summary()
        logger.info(f"=== Testing complete. Vulnerabilities found: {len(self.result)} ===")
        return self.result


if __name__ == '__main__':
    tester = JuiceShopSQLi()
    tester.run_all_tests()
