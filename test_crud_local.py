import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------------------------
# CONFIGURACIÓN DEL ENTORNO
# ---------------------------------------------------------
CURRENT_DIR = os.getcwd()
LOCAL_PATH = os.path.join(CURRENT_DIR, "index.html")
URL_BASE = f"file:///{LOCAL_PATH.replace(os.sep, '/')}"

# Datos de prueba
ADMIN_USER = "admin"
ADMIN_PASS = "12345"
STUDENT_NAME = "Estudiante QA"
STUDENT_CODE = "HU-02"
UPDATED_NAME = "Estudiante QA Actualizado"

EVIDENCE_DIR = "evidencias_historias"
if not os.path.exists(EVIDENCE_DIR):
    os.makedirs(EVIDENCE_DIR)

# ---------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------
@pytest.fixture(scope="module")
def driver():
    print(f"\n[INFO] Ejecutando pruebas sobre: {URL_BASE}")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)
    yield driver
    driver.quit()

def take_screenshot(driver, name):
    path = os.path.join(EVIDENCE_DIR, f"{name}.png")
    driver.save_screenshot(path)

# ---------------------------------------------------------
# PRUEBAS AUTOMATIZADAS POR HU
# ---------------------------------------------------------

def test_HU01_autenticacion_admin(driver):
    """HU-01: Login exitoso"""
    driver.get(URL_BASE)
    
    driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
    driver.find_element(By.ID, "btn-login").click()
    
    dashboard = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "dashboard-section"))
    )
    assert dashboard.is_displayed(), "El Dashboard debería ser visible"
    take_screenshot(driver, "HU01_Login_Exitoso")

def test_HU02_registrar_estudiante(driver):
    """HU-02: Registrar Nuevo Estudiante (Happy Path)"""
    driver.find_element(By.ID, "student-name").send_keys(STUDENT_NAME)
    driver.find_element(By.ID, "student-code").send_keys(STUDENT_CODE)
    
    driver.find_element(By.ID, "student-grade").click()
    driver.find_element(By.XPATH, "//option[@value='10']").click()
    
    driver.find_element(By.ID, "btn-save").click()
    
    # Validar éxito
    success_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "success-msg"))
    )
    assert success_msg.is_displayed()
    
    # Validar en tabla
    table_text = driver.find_element(By.ID, "student-table-body").text
    assert STUDENT_NAME in table_text
    take_screenshot(driver, "HU02_Registro_Exitoso")

def test_HU02_validacion_negativa(driver):
    """HU-02: Validación Negativa (Campos vacíos)"""
    time.sleep(2) 
    
    driver.find_element(By.ID, "btn-save").click()
    
    error_msg = driver.find_element(By.ID, "form-error")
    assert error_msg.is_displayed()
    take_screenshot(driver, "HU02_Validacion_Error")

def test_HU03_busqueda_limites(driver):
    """HU-03: Búsqueda y Limpieza de tabla"""
    long_string = "X" * 150
    
    search_input = driver.find_element(By.ID, "search-input")
    search_input.clear()
    search_input.send_keys(long_string)
    
    # Verificar que salió el mensaje "No records"
    no_records = WebDriverWait(driver, 3).until(
        EC.visibility_of_element_located((By.ID, "no-records"))
    )
    assert no_records.is_displayed()
    take_screenshot(driver, "HU03_Busqueda_Limite")
    
    # --- LIMPIEZA CRÍTICA (CORREGIDA) ---
    # 1. Limpiar input
    search_input.clear()
    # 2. Enviar un espacio y borrarlo para forzar el evento de teclado (keyup)
    search_input.send_keys(" ") 
    search_input.send_keys(Keys.BACK_SPACE) 
    
    # 3. ESPERA OBLIGATORIA: Esperar a que "No records" desaparezca
    # Esto garantiza que la tabla volvió antes de pasar al siguiente test
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located((By.ID, "no-records"))
    )

def test_HU04_editar_estudiante(driver):
    """HU-04: Editar Información (Update)"""
    # XPath robusto buscando el texto exacto del estudiante
    xpath_edit = f"//td[contains(text(), '{STUDENT_NAME}')]/..//button[contains(@class, 'edit-btn')]"
    
    # Esperar explícitamente a que el botón sea cliqueable (por si la animación tarda)
    edit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, xpath_edit))
    )
    edit_btn.click()
    
    # Validaciones UI
    assert "Editar Estudiante" in driver.find_element(By.ID, "form-title").text
    assert "Actualizar Datos" in driver.find_element(By.ID, "btn-save").text
    
    # Editar
    driver.find_element(By.ID, "student-name").clear()
    driver.find_element(By.ID, "student-name").send_keys(UPDATED_NAME)
    driver.find_element(By.ID, "btn-save").click()
    
    # Validar
    time.sleep(1)
    table_text = driver.find_element(By.ID, "student-table-body").text
    assert UPDATED_NAME in table_text
    assert STUDENT_NAME not in table_text
    take_screenshot(driver, "HU04_Edicion_Completa")

def test_HU05_eliminar_estudiante(driver):
    """HU-05: Eliminar Estudiante (Delete)"""
    # Buscar el botón eliminar del estudiante YA ACTUALIZADO
    xpath_delete = f"//td[contains(text(), '{UPDATED_NAME}')]/..//button[contains(@class, 'delete-btn')]"
    
    delete_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, xpath_delete))
    )
    delete_btn.click()
    
    # Confirmar alerta
    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert.accept()
    
    # Validar eliminación
    time.sleep(1)
    table_text = driver.find_element(By.ID, "student-table-body").text
    assert UPDATED_NAME not in table_text
    take_screenshot(driver, "HU05_Eliminacion_Exitosa")