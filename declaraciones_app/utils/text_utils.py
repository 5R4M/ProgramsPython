class NumeroATexto:
    """Clase para convertir números a texto en español"""
    
    @staticmethod
    def convertir(num: int) -> str:
        """Convierte un número a texto"""
        if num < 100:
            return NumeroATexto._numero_a_texto(num)
        elif num < 1000:
            return NumeroATexto._numero_a_texto_centenas(num)
        else:
            return NumeroATexto._convertir_numero_miles(num)
    
    @staticmethod
    def _numero_a_texto(num: int) -> str:
        """Convierte números de 0 a 99 a texto"""
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
        
        centenas_texto = ["", "ciento", "doscientos", "trescientos", "cuatrocientos",
                          "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        
        c = num // 100
        resto = num % 100
        
        if num == 100:
            return "cien"
        
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
        if miles == 1:
            texto_partes.append("mil")
        else:
            texto_partes.append(NumeroATexto._numero_a_texto(miles) + " mil")
        
        if resto > 0:
            texto_partes.append(NumeroATexto._numero_a_texto_centenas(resto))
        
        return " ".join(texto_partes)
    
    @staticmethod
    def convertir_dpi(dpi: str) -> str:
        """Convierte un DPI a texto"""
        dpi_limpio = dpi.replace(" ", "")
        
        if len(dpi_limpio) == 13 and dpi_limpio.isdigit():
            partes = [dpi_limpio[:4], dpi_limpio[4:9], dpi_limpio[9:13]]
        else:
            partes = dpi.strip().split()
            if len(partes) != 3:
                return dpi
        
        resultado = []
        
        for i, parte in enumerate(partes):
            if not parte.isdigit():
                resultado.append(parte)
                continue
            
            num = int(parte)
            
            if i == 0:  # Primera parte (año)
                if num >= 2000:
                    resto = num - 2000
                    if resto == 0:
                        resultado.append("dos mil")
                    else:
                        if resto >= 100:
                            resultado.append("dos mil " + NumeroATexto._numero_a_texto_centenas(resto))
                        else:
                            resultado.append("dos mil " + NumeroATexto._numero_a_texto(resto))
                elif num >= 1000:
                    resultado.append(NumeroATexto._convertir_numero_miles(num))
                else:
                    resultado.append(NumeroATexto._numero_a_texto_centenas(num))
            
            elif i == 1:  # Segunda parte (código municipal)
                if parte.startswith("0") and len(parte) == 5:
                    resto_num = int(parte[1:])
                    if resto_num == 0:
                        resultado.append("cero cero")
                    else:
                        resultado.append("cero " + NumeroATexto._convertir_numero_miles(resto_num))
                else:
                    resultado.append(NumeroATexto._convertir_numero_miles(num))
            
            elif i == 2:  # Tercera parte (correlativo)
                if parte.startswith("0") and len(parte) == 4:
                    resto_num = int(parte[1:])
                    if resto_num == 0:
                        resultado.append("cero cero")
                    else:
                        resultado.append("cero " + NumeroATexto._numero_a_texto_centenas(resto_num))
                else:
                    if num == 0:
                        resultado.append("cero")
                    else:
                        resultado.append(NumeroATexto._convertir_numero_miles(num))
        
        return " espacio ".join(resultado)