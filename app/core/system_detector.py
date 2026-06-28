class SystemDetector:

    @staticmethod
    def detect_os(output: str) -> str:
        """
        Detecta el sistema operativo basado en uname
        """
        output = output.lower()

        if "aix" in output:
            return "AIX"

        if "linux" in output:
            return "Linux"

        return "Unknown"