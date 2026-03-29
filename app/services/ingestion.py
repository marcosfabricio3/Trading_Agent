import time

class SignalListener:
    """
    Clase base para escuchadores de señales.
    Sigue el patrón Observer: cuando llega una señal, notifica al engine.
    """
    def __init__(self, engine):
        self.engine = engine
        self.running = False

    def start(self):
        self.running = True
        print("[Ingestion] Iniciando escucha de señales...")

    def stop(self):
        self.running = False
        print("[Ingestion] Deteniendo escucha.")

class MockListener(SignalListener):
    """
    Escuchador de prueba que simula la llegada de señales periódicas.
    """
    def listen_and_process(self, signals: list):
        self.start()
        for signal_text in signals:
            if not self.running:
                break
            
            print(f"\n[Ingestion] Nueva señal recibida del proveedor...")
            self.engine.process_signal(signal_text)
            
            # Simulamos un pequeño retraso entre señales
            time.sleep(1)
        
        self.stop()
