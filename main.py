# ================================================
# FILE: main.py
# ================================================
# Este es el punto de entrada principal de la aplicación.
# Su única función es crear una instancia de la ventana principal (SeatPlanApp)
# y ejecutarla para que se muestre la interfaz gráfica.

from gui.window import SeatPlanApp

if __name__ == "__main__":
    # Crea una instancia de la aplicación de la interfaz gráfica.
    app = SeatPlanApp()
    # Inicia el bucle de eventos de la aplicación. La ventana será visible
    # y el programa esperará la interacción del usuario.
    app.run()