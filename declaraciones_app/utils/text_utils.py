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
        # CORRECCIÓN: Si el número es >= 1000, usar el método de miles
        if num >= 1000:
            return NumeroATexto._convertir_numero_miles(num)
        
        if num < 100:
            return NumeroATexto._numero_a_texto(num)
        
        centenas_texto = ["", "ciento", "doscientos", "trescientos", "cuatrocientos",
                          "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        
        c = num // 100
        resto = num % 100
        
        if num == 100:
            return "cien"
        
        # CORRECCIÓN: Validar que c esté en el rango válido
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
        if miles == 1:
            texto_partes.append("mil")
        else:
            # CORRECCIÓN: Usar el método correcto según el tamaño de 'miles'
            if miles < 100:
                texto_partes.append(NumeroATexto._numero_a_texto(miles) + " mil")
            elif miles < 1000:
                texto_partes.append(NumeroATexto._numero_a_texto_centenas(miles) + " mil")
            else:
                # Para números muy grandes (millones)
                texto_partes.append(str(miles) + " mil")
        
        if resto > 0:
            texto_partes.append(NumeroATexto._numero_a_texto_centenas(resto))
        
        return " ".join(texto_partes)
    
    @staticmethod
    def convertir_dpi(dpi: str) -> str:
        """Convierte un DPI a texto"""
        # Limpiar el DPI
        dpi_limpio = dpi.replace(" ", "").strip()
        
        # Validar que sea numérico y tenga 13 dígitos
        if not dpi_limpio.isdigit():
            return dpi
        
        if len(dpi_limpio) != 13:
            return dpi
        
        # Separar en partes: AAAA MMMMM CCCC
        partes = [dpi_limpio[:4], dpi_limpio[4:9], dpi_limpio[9:13]]
        
        resultado = []
        
        for i, parte in enumerate(partes):
            if not parte.isdigit():
                resultado.append(parte)
                continue
            
            num = int(parte)
            
            if i == 0:  # Primera parte (año) - 4 dígitos
                # CORRECCIÓN: Manejar años de 4 dígitos correctamente
                if num >= 3000:
                    # Ejemplo: 3445 = tres mil cuatrocientos cuarenta y cinco
                    resultado.append(NumeroATexto._convertir_numero_miles(num))
                elif num >= 2000:
                    resto = num - 2000
                    if resto == 0:
                        resultado.append("dos mil")
                    else:
                        # CORRECCIÓN: Usar el método correcto según el tamaño
                        if resto >= 1000:
                            resultado.append("dos mil " + NumeroATexto._convertir_numero_miles(resto))
                        elif resto >= 100:
                            resultado.append("dos mil " + NumeroATexto._numero_a_texto_centenas(resto))
                        else:
                            resultado.append("dos mil " + NumeroATexto._numero_a_texto(resto))
                elif num >= 1000:
                    resultado.append(NumeroATexto._convertir_numero_miles(num))
                else:
                    resultado.append(NumeroATexto._numero_a_texto_centenas(num))
            
            elif i == 1:  # Segunda parte (código municipal) - 5 dígitos
                if parte.startswith("0") and len(parte) == 5:
                    resto_num = int(parte[1:])
                    if resto_num == 0:
                        resultado.append("cero cero")
                    else:
                        resultado.append("cero " + NumeroATexto._convertir_numero_miles(resto_num))
                else:
                    resultado.append(NumeroATexto._convertir_numero_miles(num))
            
            elif i == 2:  # Tercera parte (correlativo) - 4 dígitos
                if parte.startswith("0") and len(parte) == 4:
                    resto_num = int(parte[1:])
                    if resto_num == 0:
                        resultado.append("cero cero")
                    else:
                        # CORRECCIÓN: Usar convertir() general que maneja todos los tamaños
                        resultado.append("cero " + NumeroATexto.convertir(resto_num))
                else:
                    if num == 0:
                        resultado.append("cero")
                    else:
                        resultado.append(NumeroATexto._convertir_numero_miles(num))
        
        return " espacio ".join(resultado)