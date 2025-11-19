
import socket
import pickle
import numpy as np
import time
import sys

class ClienteMultiplicacao:
    def __init__(self, host='localhost', port=5000):
        """
        Inicializa o cliente de multiplicacao de matrizes
        
        Args:
            host: Endereco do servidor
            port: Porta do servidor
        """
        self.host = host
        self.port = port
        self.socket_cliente = None
        
    def conectar_servidor(self):
        """Conecta ao servidor"""
        print(f"[CONECTANDO] Ao servidor {self.host}:{self.port}...")
        
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        tentativas = 0
        max_tentativas = 5
        
        while tentativas < max_tentativas:
            try:
                self.socket_cliente.connect((self.host, self.port))
                print("[OK] Conectado com sucesso!")
                return True
            except ConnectionRefusedError:
                tentativas += 1
                if tentativas < max_tentativas:
                    print(f"[TENTATIVA] {tentativas}/{max_tentativas}... Aguardando servidor...")
                    time.sleep(2)
                else:
                    print(f"[ERRO] Falha ao conectar apos {max_tentativas} tentativas")
                    return False
            except Exception as e:
                print(f"[ERRO] Ao conectar: {e}")
                return False
                
    def receber_trabalho(self):
        """
        Recebe trabalho do servidor
        
        Returns:
            Dicionario com id_cliente, particao_A e matriz_B
        """
        print("\n[AGUARDANDO] Trabalho do servidor...")
        
        # Recebe tamanho dos dados
        tamanho_bytes = self.socket_cliente.recv(4)
        if not tamanho_bytes:
            return None
            
        tamanho = int.from_bytes(tamanho_bytes, byteorder='big')
        
        # Recebe dados
        dados = b''
        while len(dados) < tamanho:
            pacote = self.socket_cliente.recv(min(4096, tamanho - len(dados)))
            if not pacote:
                break
            dados += pacote
            
        trabalho = pickle.loads(dados)
        
        id_cliente = trabalho['id_cliente']
        particao_A = trabalho['particao_A']
        matriz_B = trabalho['matriz_B']
        
        print(f"[RECEBIDO] Trabalho!")
        print(f"   - ID do Cliente: {id_cliente}")
        print(f"   - Particao A: {particao_A.shape}")
        print(f"   - Matriz B: {matriz_B.shape}")
        print(f"   - Tamanho recebido: {tamanho / 1024:.2f} KB")
        
        return trabalho
    
    def multiplicar_parcial(self, particao_A, matriz_B):
        """
        Executa multiplicacao parcial de matrizes
        
        Args:
            particao_A: Submatriz de A
            matriz_B: Matriz B completa
            
        Returns:
            Resultado parcial da multiplicacao
        """
        print(f"\n[CALCULANDO] Iniciando calculo...")
        print(f"   Operacao: A_parcial{particao_A.shape} x B{matriz_B.shape}")
        print(f"   Total de operacoes: {particao_A.shape[0] * particao_A.shape[1] * matriz_B.shape[1]} multiplicacoes")
        
        tempo_inicio = time.time()
        
        print(f"\n   >>> EXECUTANDO MULTIPLICACAO MATRICIAL <<<")
        print(f"   >>> C_parcial = A_parcial x B <<<")
        print(f"   >>> Usando NumPy (np.dot) <<<\n")
        
        # Realiza multiplicacao matricial
        resultado = np.dot(particao_A, matriz_B)
        
        tempo_fim = time.time()
        tempo_calculo = tempo_fim - tempo_inicio
        
        print(f"[OK] MULTIPLICACAO CONCLUIDA em {tempo_calculo:.4f} segundos")
        print(f"   Resultado: {resultado.shape}")
        print(f"   Primeiros elementos do resultado:")
        print(f"   {resultado[0] if len(resultado) > 0 else 'N/A'}")
        
        return resultado
    
    def enviar_resultado(self, resultado):
        """
        Envia resultado de volta ao servidor
        
        Args:
            resultado: Matriz resultado parcial
        """
        print(f"\n[ENVIANDO] Resultado para o servidor...")
        
        dados_serializados = pickle.dumps(resultado)
        tamanho = len(dados_serializados)
        
        # Envia tamanho dos dados
        self.socket_cliente.sendall(tamanho.to_bytes(4, byteorder='big'))
        
        # Envia dados
        self.socket_cliente.sendall(dados_serializados)
        
        print(f"[OK] Resultado enviado ({tamanho / 1024:.2f} KB)")
        
    def processar(self):
        """Processa trabalho recebido do servidor"""
        try:
            # Recebe trabalho
            trabalho = self.receber_trabalho()
            
            if trabalho is None:
                print("[ERRO] Nenhum trabalho recebido")
                return False
                
            id_cliente = trabalho['id_cliente']
            particao_A = trabalho['particao_A']
            matriz_B = trabalho['matriz_B']
            
            print("\n" + "="*60)
            print(f"[PROCESSANDO] TRABALHO (Cliente {id_cliente})")
            print("="*60)
            
            # Executa multiplicacao parcial
            resultado = self.multiplicar_parcial(particao_A, matriz_B)
            
            # Envia resultado
            self.enviar_resultado(resultado)
            
            print("="*60)
            print("[CONCLUIDO] TRABALHO FINALIZADO!")
            print("="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n[ERRO] Ao processar: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def fechar_conexao(self):
        """Fecha conexao com servidor"""
        if self.socket_cliente:
            self.socket_cliente.close()
            print("[FECHADO] Conexao encerrada.\n")


def main():
    """Funcao principal do cliente"""
    print("\n" + "="*60)
    print("  SISTEMA DE MULTIPLICACAO DISTRIBUIDA DE MATRIZES")
    print("  Modo: CLIENTE")
    print("="*60 + "\n")
    
    # Configuracoes
    HOST = 'localhost'
    PORT = 5000
    
    # Permite passar host e porta como argumentos
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    
    # Cria cliente
    cliente = ClienteMultiplicacao(HOST, PORT)
    
    try:
        # Conecta ao servidor
        if not cliente.conectar_servidor():
            return
            
        # Processa multiplos trabalhos
        print("\n[PRONTO] Cliente pronto para processar trabalhos...")
        
        # Primeiro trabalho
        if not cliente.processar():
            return
            
        # Aguarda um pouco antes do proximo trabalho
        time.sleep(1)
        
        # Segundo trabalho (matrizes maiores)
        if not cliente.processar():
            return
        
        print("[SUCESSO] Todos os trabalhos processados!")
        
    except KeyboardInterrupt:
        print("\n\n[INTERROMPIDO] Pelo usuario")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cliente.fechar_conexao()


if __name__ == "__main__":
    main()