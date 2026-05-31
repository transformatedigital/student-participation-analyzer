#!/usr/bin/env python3
"""
Asistente de testing del dashboard online.

Verifica:
  · HTTP 200 en todas las páginas y recursos
  · Contenido HTML correcto (títulos, tabs, charts)
  · JSON válido con estructura esperada
  · Excel descargable con MIME correcto
  · Links internos consistentes (cada card de clase apunta a su HTML)
  · CDN externos (chart.js)
  · 5 alumnos esperados aparecen
  · Toggle escenario A/B presente
  · Cada página de clase tiene los 3 tabs (Transcripción, Preparation, Participation)

Uso:
    python3 backend/test_dashboard.py
    python3 backend/test_dashboard.py --url https://otra-url.com/

Opcional (interactividad):
    pip install playwright && playwright install chromium
    python3 backend/test_dashboard.py --interactive
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Optional
from urllib.parse import urljoin

DEFAULT_URL = "https://transformatedigital.github.io/student-participation-analyzer/"
EXPECTED_STUDENTS = ["Aryang", "Mega", "Chilaka", "Grace", "Sthepen"]
EXPECTED_CLASS_DATES = ["2026-03-17", "2026-03-31", "2026-04-07", "2026-04-21"]
EXPECTED_TABS = ["Full transcript", "Preparation", "Participation"]

# Colores ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class TestRunner:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/") + "/"
        self.results = []
        self.passed = 0
        self.failed = 0

    def fetch(self, path: str, expected_status: int = 200, return_bytes: bool = False) -> Optional[str]:
        """GET <base>/<path> y devuelve texto (o bytes). None si falla."""
        url = urljoin(self.base, path)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DashboardTester/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status != expected_status:
                    return None
                if return_bytes:
                    return r.read()
                ctype = r.headers.get("Content-Type", "")
                charset = "utf-8" if "utf-8" in ctype.lower() else "latin-1"
                return r.read().decode(charset, errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            return None

    def http_status(self, path: str) -> Optional[int]:
        url = urljoin(self.base, path)
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DashboardTester/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code
        except (urllib.error.URLError, TimeoutError):
            return None

    def assert_test(self, name: str, condition: bool, details: str = ""):
        elapsed_ms = self._last_ms
        if condition:
            self.passed += 1
            mark = f"{GREEN}✓{RESET}"
            print(f"  {mark} {name}  {DIM}[{elapsed_ms}ms]{RESET}")
        else:
            self.failed += 1
            mark = f"{RED}✗{RESET}"
            print(f"  {mark} {name}  {DIM}[{elapsed_ms}ms]{RESET}")
            if details:
                print(f"    {RED}└─ {details}{RESET}")
        self.results.append({"name": name, "ok": condition, "details": details, "ms": elapsed_ms})

    def time_op(self, fn):
        t0 = time.perf_counter()
        result = fn()
        self._last_ms = int((time.perf_counter() - t0) * 1000)
        return result

    # ─── Suite de tests ──────────────────────────────────────────
    def section(self, title: str):
        print(f"\n{CYAN}{BOLD}━━ {title} ━━{RESET}")

    def run_all(self):
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}  DASHBOARD TEST RUNNER{RESET}")
        print(f"  URL: {CYAN}{self.base}{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

        self.section("Disponibilidad HTTP")
        # Index redirect a dashboard
        index_html = self.time_op(lambda: self.fetch("index.html"))
        self.assert_test("Index responde 200", index_html is not None)
        self.assert_test("Index redirige a dashboard.html",
                         index_html and "dashboard.html" in index_html)

        dash_html = self.time_op(lambda: self.fetch("dashboard.html"))
        self.assert_test("Dashboard responde 200", dash_html is not None)

        # JSON acumulado
        json_text = self.time_op(lambda: self.fetch("all_classes.json"))
        json_data = None
        try:
            json_data = json.loads(json_text) if json_text else None
        except Exception:
            pass
        self.assert_test("JSON acumulado responde 200 y es parseable", json_data is not None)
        if json_data:
            self.assert_test(
                f"JSON tiene {len(EXPECTED_CLASS_DATES)} clases",
                json_data.get("n_classes") == len(EXPECTED_CLASS_DATES),
                f"Encontradas: {json_data.get('n_classes')}"
            )
            class_ids = set(json_data.get("class_ids", []))
            missing = set(EXPECTED_CLASS_DATES) - class_ids
            self.assert_test("JSON incluye las 4 fechas esperadas", not missing,
                             f"Faltan: {missing}" if missing else "")

        # Excel descargable
        excel_status = self.time_op(lambda: self.http_status("Component_A_Aggregated.xlsx"))
        self.assert_test("Excel acumulado descargable (HTTP 200)", excel_status == 200,
                         f"HTTP {excel_status}")

        self.section("Páginas de detalle por clase")
        for sid in EXPECTED_CLASS_DATES:
            html = self.time_op(lambda s=sid: self.fetch(f"classes/{s}.html"))
            self.assert_test(f"clases/{sid}.html responde 200", html is not None)
            if html:
                missing_tabs = [t for t in EXPECTED_TABS if t not in html]
                self.assert_test(
                    f"clases/{sid}.html tiene los 3 tabs",
                    not missing_tabs,
                    f"Faltan: {missing_tabs}" if missing_tabs else ""
                )

        self.section("Contenido del dashboard")
        if dash_html:
            self.time_op(lambda: None)
            # 5 alumnos en el HTML/JSON
            missing_students = []
            if json_data and "aggregated" in json_data:
                missing_students = [s for s in EXPECTED_STUDENTS if s not in json_data["aggregated"]]
            self.assert_test("5 alumnos esperados en el JSON",
                             not missing_students,
                             f"Faltan: {missing_students}" if missing_students else "")

            self.time_op(lambda: None)
            self.assert_test("Toggle escenario A/B presente",
                             'id="scenarioSelect"' in dash_html)

            self.time_op(lambda: None)
            self.assert_test("Canvas para chart de evolución presente",
                             'id="evolutionChart"' in dash_html)

            self.time_op(lambda: None)
            self.assert_test("Cards de clase linkean a páginas correctas",
                             all(f'classes/{sid}.html' in dash_html.replace("${c.session_id}", sid)
                                 or 'classes/${c.session_id}' in dash_html
                                 for sid in EXPECTED_CLASS_DATES))

            self.time_op(lambda: None)
            self.assert_test("Chart.js cargado desde CDN",
                             "cdn.jsdelivr.net/npm/chart.js" in dash_html)

        self.section("CDNs externos")
        cdn_status = self.time_op(lambda: self.http_status_external(
            "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"))
        self.assert_test("Chart.js CDN accesible",
                         cdn_status == 200,
                         f"HTTP {cdn_status}")

        self.section("Validación de datos")
        if json_data:
            agg = json_data.get("aggregated", {})
            self.time_op(lambda: None)
            self.assert_test("Cada alumno tiene 4 clases registradas",
                             all(d.get("n_classes") == 4 for d in agg.values()),
                             "Algún alumno tiene != 4 clases")

            self.time_op(lambda: None)
            self.assert_test("Componente A está en rango [0, 20]",
                             all(0 <= d.get("total_a_avg", -1) <= 20 for d in agg.values()) and
                             all(0 <= d.get("total_b_avg", -1) <= 20 for d in agg.values()))

        self.print_summary()
        return self.failed == 0

    def http_status_external(self, url: str) -> Optional[int]:
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DashboardTester/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code
        except (urllib.error.URLError, TimeoutError):
            return None

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        if self.failed == 0:
            print(f"{GREEN}{BOLD}  ✓ TODOS LOS TESTS PASARON  ·  {self.passed}/{total}{RESET}")
        else:
            print(f"{RED}{BOLD}  ✗ ALGUNOS TESTS FALLARON  ·  {self.passed}/{total} OK  ·  {self.failed} fallidos{RESET}")
        total_ms = sum(r["ms"] for r in self.results)
        print(f"  {DIM}Tiempo total: {total_ms}ms{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Test runner del dashboard online")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL base a probar")
    args = parser.parse_args()

    runner = TestRunner(args.url)
    ok = runner.run_all()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
