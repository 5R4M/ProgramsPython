class NumeroATexto:
    """Clase para convertir números a texto en español"""
    
    @staticmethod
    def convertir(num: int) -> str:
        """Convierte un número a texto"""
        if num == 0:
            return "cero"
        elif num < 100:
            return NumeroATexto._numero_a_texto(num)
        elif num < 1000:
            return NumeroATexto._numero_a_texto_centenas(num)
        else:
            return NumeroATexto._convertir_numero_miles(num)
    
    @staticmethod
    def _numero_a_texto(num: int) -> str:
        """Convierte números de 0 a 99 a texto"""
        if num == 0:
            return "cero"
            
        unidades = ["", "uno", "dos", "tres", "cuatro", "cinco",
                    "seis", "siete", "ocho", "nueve"]
        decenas = ["", "diez", "veinte", "treinta", "cuarenta",
                   "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
        especiales = ["diez", "once", "doce", "trece", "catorce",
                      "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve"]

        if num < 10:
            return unidades[num]
        if 10 <= num < 20:
            return especiales[num - 10]
        if 20 <= num < 30:
            if num == 20:
                return "veinte"
            return "veinti" + unidades[num - 20]
        if num < 100:
            d = num // 10
            u = num % 10
            if u == 0:
                return decenas[d]
            return f"{decenas[d]} y {unidades[u]}"
        return str(num)
    
    @staticmethod
    def _numero_a_texto_centenas(num: int) -> str:
        """Convierte números de 100 a 999 a texto"""
        if num < 100:
            return NumeroATexto._numero_a_texto(num)
        
        if num >= 1000:
            return NumeroATexto._convertir_numero_miles(num)
        
        centenas_texto = ["", "ciento", "doscientos", "trescientos", "cuatrocientos",
                          "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        
        c = num // 100
        resto = num % 100
        
        if num == 100:
            return "cien"
        
        if c > 9:
            return NumeroATexto._convertir_numero_miles(num)
        
        resultado = centenas_texto[c]
        if resto > 0:
            resultado += " " + NumeroATexto._numero_a_texto(resto)
        
        return resultado
    
    @staticmethod
    def _convertir_numero_miles(num: int) -> str:
        """Convierte números de 1000 en adelante a texto"""
        if num < 1000:
            return NumeroATexto._numero_a_texto_centenas(num)
        
        miles = num // 1000
        resto = num % 1000
        
        texto_partes = []
        
        # CORRECCIÓN CRÍTICA: Usar "un mil" para 1000-1999
        if miles == 1:
            texto_partes.append("un mil")
        else:
            if miles < 100:
                texto_partes.append(NumeroATexto._numero_a_texto(miles) + " mil")
            elif miles < 1000:
                texto_partes.append(NumeroATexto._numero_a_texto_centenas(miles) + " mil")
            else:
                texto_partes.append(str(miles) + " mil")
        
        if resto > 0:
            texto_partes.append(NumeroATexto._numero_a_texto_centenas(resto))
        
        return " ".join(texto_partes)
    
    @staticmethod
    def convertir_dpi(dpi: str) -> str:
        """
        Convierte un DPI a texto con la palabra "espacio" como separador.
        Lee ceros iniciales individualmente, luego el resto como número completo.
        Ejemplo: "1916 02426 0101" -> "un mil novecientos dieciséis espacio cero dos mil cuatrocientos veintiséis espacio cero ciento uno"
        """
        # Limpiar el DPI
        dpi_limpio = dpi.replace(" ", "").strip()
        
        # Validar que sea numérico y tenga 13 dígitos
        if not dpi_limpio.isdigit():
            return dpi
        
        if len(dpi_limpio) != 13:
            return dpi
        
        # Separar en tres partes: XXXX XXXXX XXXX
        parte1 = dpi_limpio[0:4]    # Primeros 4 dígitos
        parte2 = dpi_limpio[4:9]    # Siguientes 5 dígitos
        parte3 = dpi_limpio[9:13]   # Últimos 4 dígitos
        
        resultado = []
        
        # ===== PROCESAR CADA PARTE =====
        for parte in [parte1, parte2, parte3]:
            parte_resultado = []
            
            # Contar cuántos ceros hay al inicio
            ceros_iniciales = 0
            for digit in parte:
                if digit == '0':
                    ceros_iniciales += 1
                else:
                    break
            
            # Si toda la parte son ceros
            if ceros_iniciales == len(parte):
                parte_resultado = ['cero'] * len(parte)
            else:
                # Agregar los ceros iniciales uno por uno
                for _ in range(ceros_iniciales):
                    parte_resultado.append('cero')
                
                # Convertir el resto como número completo
                resto = parte[ceros_iniciales:]
                if resto:  # Si hay algo después de los ceros
                    numero = int(resto)
                    if numero > 0:
                        parte_resultado.append(NumeroATexto.convertir(numero))
            
            # Unir los elementos de esta parte
            resultado.append(' '.join(parte_resultado))
        
        # Unir las tres partes con la palabra "espacio"
        return ' espacio '.join(resultado)
    
    @staticmethod
    def convertir_dpi_con_separador_espacio(dpi: str) -> str:
        """
        Igual que convertir_dpi pero usa " espacio " como separador entre partes
        Lee ceros iniciales individualmente, luego el resto como número completo.
        """
        dpi_limpio = dpi.replace(" ", "").strip()
        
        if not dpi_limpio.isdigit() or len(dpi_limpio) != 13:
            return dpi
        
        parte1 = dpi_limpio[0:4]
        parte2 = dpi_limpio[4:9]
        parte3 = dpi_limpio[9:13]
        
        resultado = []
        
        for parte in [parte1, parte2, parte3]:
            parte_resultado = []
            
            # Contar cuántos ceros hay al inicio
            ceros_iniciales = 0
            for digit in parte:
                if digit == '0':
                    ceros_iniciales += 1
                else:
                    break
            
            # Si toda la parte son ceros
            if ceros_iniciales == len(parte):
                parte_resultado = ['cero'] * len(parte)
            else:
                # Agregar los ceros iniciales
                for _ in range(ceros_iniciales):
                    parte_resultado.append('cero')
                
                # Convertir el resto como número completo
                resto = parte[ceros_iniciales:]
                if resto:
                    numero = int(resto)
                    if numero > 0:
                        parte_resultado.append(NumeroATexto.convertir(numero))
            
            resultado.append(' '.join(parte_resultado))
        
        return ' espacio '.join(resultado)


# ===== PRUEBAS =====
if __name__ == "__main__":
    print("=" * 80)
    print("PRUEBAS DE CONVERSIÓN DE DPI A TEXTO")
    print("=" * 80)
    print()
    
    # Casos de prueba
    casos_prueba = [
        "1916 02426 0101",  # Nuevo caso específico
        "1916 00640 0101",
        "1916 00024 2658",
        "2345 12000 3456",
        "1000 00001 0001",
    ]
    
    for dpi in casos_prueba:
        print(f"DPI: {dpi}")
        print(f"Texto: {NumeroATexto.convertir_dpi(dpi)}")
        print("-" * 80)
        print()
    
    # Pruebas de números individuales
    print("=" * 80)
    print("PRUEBAS DE NÚMEROS INDIVIDUALES")
    print("=" * 80)
    print()
    
    numeros_prueba = [0, 24, 100, 1000, 1916, 2000, 2658]
    
    for num in numeros_prueba:
        print(f"{num:>6} = {NumeroATexto.convertir(num)}")
    
    print()
    print("=" * 80)