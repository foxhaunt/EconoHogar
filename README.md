# EconoHogar – Control de Gastos Domésticos

Aplicación de escritorio para Ubuntu que te ayuda a gestionar tu economía personal y del hogar. Registra gastos, controla tu salario, analiza en qué gastas más y visualiza tu ahorro mes a mes.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Tkinter](https://img.shields.io/badge/GUI-Tkinter-lightgrey) ![SQLite](https://img.shields.io/badge/DB-SQLite3-green) ![Platform](https://img.shields.io/badge/Platform-Ubuntu-orange)

---

## Características

| Pestaña | Descripción |
|---|---|
| **Dashboard** | Resumen del mes: KPIs (total gastado, balance, ahorro), últimos gastos y top categorías |
| **Gastos** | Añadir, editar y eliminar gastos; filtro por categoría; calendario desplegable para la fecha |
| **Gráficos** | Tarta por categoría, barras mensuales, evolución anual, gastos diarios y comparativa entre meses |
| **Ahorro** | Balance mensual, tasa de ahorro, oportunidades de mejora y proyección anual |
| **Categorías** | Crear y renombrar categorías con color personalizado |

### Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl + N` | Ir a la pestaña Gastos y enfocar el campo fecha |
| `Ctrl + Supr` | Eliminar el gasto seleccionado |
| `←` / `→` | Navegar al mes anterior / siguiente |

---

## Requisitos

- Ubuntu 20.04 o superior
- Python 3.8+
- `tkinter` (incluido en Python estándar; en Ubuntu puede requerir `python3-tk`)
- `matplotlib` (se instala automáticamente al arrancar)

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/econohogar.git
cd econohogar

# (Opcional) Instalar matplotlib manualmente si prefieres no esperar al primer arranque
pip install matplotlib
```

Si `tkinter` no está disponible:

```bash
sudo apt install python3-tk
```

---

## Uso

```bash
python3 main.py
```

`main.py` comprueba las dependencias al arrancar e instala `matplotlib` si falta. La primera vez puede tardar unos segundos.

### Primeros pasos

1. **Introduce el salario** del mes en el panel izquierdo → pulsa *Guardar salario*
2. **Añade gastos** en la pestaña *Gastos*: elige la fecha con el calendario 📅, selecciona categoría, escribe una descripción e importe
3. **Edita un gasto** haciendo doble clic sobre cualquier fila de la lista
4. **Explora los gráficos** para ver cómo distribuyes el dinero
5. **Cambia de mes** con los controles de mes/año del panel izquierdo o con `←` / `→`

---

## Dónde se guardan los datos

Los datos se almacenan en una base de datos SQLite en tu directorio home:

```
~/.econohogar.db
```

La aplicación crea automáticamente una copia de seguridad diaria (máximo una por semana) en:

```
~/.econohogar_backup_AAAA-MM-DD.db
```

---

## Añadir al escritorio de Ubuntu

```bash
# Edita la ruta en econohogar.desktop si instalaste en otra carpeta
nano econohogar.desktop   # cambia la línea Exec= con la ruta correcta

# Copia el lanzador al escritorio
cp econohogar.desktop ~/Desktop/
chmod +x ~/Desktop/econohogar.desktop
```

---

## Estructura del proyecto

```
econohogar/
├── main.py              # Lanzador: comprueba dependencias y arranca gastos.py
├── gastos.py            # Aplicación completa (UI + lógica + datos)
├── migrate_econohogar.py # Migración de datos desde versiones anteriores (JSON → SQLite)
├── econohogar.desktop   # Acceso directo para el escritorio de Ubuntu
└── ~/.econohogar.db     # Base de datos SQLite (generada automáticamente)
```

---

## Stack técnico

- **GUI:** Tkinter + ttk (widgets nativos del sistema)
- **Gráficos:** matplotlib con backend TkAgg embebido en la ventana
- **Base de datos:** SQLite3 con WAL mode y foreign keys
- **Lenguaje:** Python 3, sin frameworks externos

---

## Licencia

MIT
