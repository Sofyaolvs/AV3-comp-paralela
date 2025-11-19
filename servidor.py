

import socket
import pickle
import threading
import numpy as np
import time
from typing import List, Tuple

class ServidorMultiplicacao:
    def __init__(self, host='localhost', port=5000):
        """
        Inicializa o servidor de multiplicacao de matrizes
        
        Args:
            host: Endereco do servidor
            port: Porta para escutar conexoes
        """
        self.host = host
        self.port = port
        self.clientes = []
        self.resultados = []
        self.lock = threading.Lock()
        
    def iniciar_servidor(self):
        """Inicia o servidor e aguarda conexoes de clientes"""
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.port))
        self.socket_servidor.listen(5)
        
        print(f"[SERVIDOR] Iniciado em {self.host}:{self.port}")
        print("[AGUARDANDO] Conexoes de clientes...")
        
    def aceitar_clientes(self, num_clientes=2):
        """
        Aceita conexoes de clientes
        
        Args:
            num_clientes: Numero de clientes para aguardar
        """
        while len(self.clientes) < num_clientes:
            cliente_socket, endereco = self.socket_servidor.accept()
            self.clientes.append(cliente_socket)
            print(f"[OK] Cliente {len(self.clientes)} conectado de {endereco}")
            
        print(f"[OK] Todos os {num_clientes} clientes conectados!\n")
        
    def gerar_matrizes(self, m, n, p):
        """
        Gera matrizes aleatorias para teste
        
        Args:
            m: Linhas da matriz A
            n: Colunas da matriz A / Linhas da matriz B
            p: Colunas da matriz B
            
        Returns:
            Tupla com matriz A e matriz B
        """
        print(f"[GERANDO] Matrizes A({m}x{n}) e B({n}x{p})...")
        A = np.random.randint(1, 10, size=(m, n))
        B = np.random.randint(1, 10, size=(n, p))
        return A, B
    
    def particionar_por_linhas(self, A, num_particoes):
        """
        Particiona matriz A em grupos de linhas
        
        Args:
            A: Matriz a ser particionada
            num_particoes: Numero de particoes
            
        Returns:
            Lista de submatrizes
        """
        m = A.shape[0]
        linhas_por_particao = m // num_particoes
        particoes = []
        
        for i in range(num_particoes):
            inicio = i * linhas_por_particao
            if i == num_particoes - 1:
                # Ultima particao pega linhas restantes
                fim = m
            else:
                fim = (i + 1) * linhas_por_particao
            particoes.append(A[inicio:fim])
            
        return particoes
    
    def enviar_trabalho(self, cliente_socket, id_cliente, particao_A, B):
        """
        Envia trabalho para um cliente especifico
        
        Args:
            cliente_socket: Socket do cliente
            id_cliente: ID do cliente
            particao_A: Particao da matriz A
            B: Matriz B completa
        """
        dados = {
            'id_cliente': id_cliente,
            'particao_A': particao_A,
            'matriz_B': B
        }
        
        dados_serializados = pickle.dumps(dados)
        tamanho = len(dados_serializados)
        
        # Envia tamanho dos dados primeiro
        cliente_socket.sendall(tamanho.to_bytes(4, byteorder='big'))
        # Envia dados
        cliente_socket.sendall(dados_serializados)
        
        print(f"[ENVIADO] Trabalho para Cliente {id_cliente}")
        print(f"   - Linhas da particao: {particao_A.shape[0]}")
        print(f"   - Tamanho dos dados: {tamanho / 1024:.2f} KB")
        
    def receber_resultado(self, cliente_socket, id_cliente):
        """
        Recebe resultado de um cliente
        
        Args:
            cliente_socket: Socket do cliente
            id_cliente: ID do cliente
            
        Returns:
            Resultado parcial da multiplicacao
        """
        # Recebe tamanho dos dados
        tamanho_bytes = cliente_socket.recv(4)
        tamanho = int.from_bytes(tamanho_bytes, byteorder='big')
        
        # Recebe dados
        dados = b''
        while len(dados) < tamanho:
            pacote = cliente_socket.recv(min(4096, tamanho - len(dados)))
            if not pacote:
                break
            dados += pacote
            
        resultado = pickle.loads(dados)
        
        print(f"[RECEBIDO] Resultado do Cliente {id_cliente}")
        print(f"   - Linhas calculadas: {resultado.shape[0]}")
        
        return resultado
    
    def processar_cliente(self, cliente_socket, id_cliente, particao_A, B):
        """
        Thread para processar um cliente especifico
        
        Args:
            cliente_socket: Socket do cliente
            id_cliente: ID do cliente
            particao_A: Particao da matriz A
            B: Matriz B completa
        """
        try:
            # Envia trabalho
            self.enviar_trabalho(cliente_socket, id_cliente, particao_A, B)
            
            # Recebe resultado
            resultado = self.receber_resultado(cliente_socket, id_cliente)
            
            # Armazena resultado com lock
            with self.lock:
                self.resultados.append((id_cliente, resultado))
                
        except Exception as e:
            print(f"[ERRO] Ao processar Cliente {id_cliente}: {e}")
            
    def multiplicar_distribuido(self, A, B):
        """
        Executa multiplicacao distribuida de matrizes
        
        Args:
            A: Matriz A (m x n)
            B: Matriz B (n x p)
            
        Returns:
            Matriz resultado C (m x p)
        """
        print("\n" + "="*60)
        print("[INICIO] MULTIPLICACAO DISTRIBUIDA")
        print("="*60)
        
        num_clientes = len(self.clientes)
        print(f"[INFO] Numero de clientes: {num_clientes}")
        print(f"[INFO] Dimensoes: A{A.shape} x B{B.shape}")
        print(f"[INFO] Resultado esperado: C{(A.shape[0], B.shape[1])}")
        print(f"\n[ESTRATEGIA] Decomposicao por LINHAS (Metodologia de Foster)")
        print(f"[ESTRATEGIA] Cada cliente recebe linhas de A e toda matriz B")
        print(f"[ESTRATEGIA] Cada cliente calcula: C_parcial = A_parcial x B")
        
        # Particiona matriz A
        particoes = self.particionar_por_linhas(A, num_clientes)
        print(f"\n[PARTICIONADO] Matriz A em {num_clientes} partes")
        for i, particao in enumerate(particoes):
            print(f"   Cliente {i+1}: Linhas {particao.shape[0]} de A")
        
        # Limpa resultados anteriores
        self.resultados = []
        
        # Inicia tempo
        tempo_inicio = time.time()
        
        # Cria threads para processar cada cliente
        threads = []
        for i, (cliente_socket, particao) in enumerate(zip(self.clientes, particoes)):
            thread = threading.Thread(
                target=self.processar_cliente,
                args=(cliente_socket, i+1, particao, B)
            )
            threads.append(thread)
            thread.start()
            
        # Aguarda todas as threads
        print("\n[AGUARDANDO] Processamento dos clientes...")
        for thread in threads:
            thread.join()
            
        tempo_fim = time.time()
        tempo_total = tempo_fim - tempo_inicio
        
        # Ordena resultados por ID do cliente
        self.resultados.sort(key=lambda x: x[0])
        
        print(f"\n[AGREGANDO] Concatenando resultados parciais...")
        for id_cliente, resultado in self.resultados:
            print(f"   Cliente {id_cliente}: C_parcial{resultado.shape}")
        
        # Concatena resultados
        C = np.vstack([resultado for _, resultado in self.resultados])
        
        print(f"\n[CONCLUIDO] MULTIPLICACAO DISTRIBUIDA FINALIZADA!")
        print(f"[TEMPO] Total: {tempo_total:.4f} segundos")
        print(f"[RESULTADO] Matriz C final: {C.shape}")
        print(f"[RESULTADO] Formula: C({C.shape[0]}x{C.shape[1]}) = A({A.shape[0]}x{A.shape[1]}) x B({B.shape[0]}x{B.shape[1]})")
        print("="*60 + "\n")
        
        return C
    
    def verificar_resultado(self, A, B, C):
        """
        Verifica se o resultado esta correto comparando com numpy
        
        Args:
            A: Matriz A
            B: Matriz B
            C: Matriz resultado calculada
        """
        print("\n[VERIFICANDO] Resultado...")
        C_esperado = np.dot(A, B)
        
        if np.allclose(C, C_esperado):
            print("[OK] Resultado CORRETO! A multiplicacao distribuida funcionou.")
        else:
            print("[ERRO] Resultado INCORRETO! Ha diferencas no calculo.")
            diferenca_max = np.max(np.abs(C - C_esperado))
            print(f"   Diferenca maxima: {diferenca_max}")
            
    def fechar_conexoes(self):
        """Fecha todas as conexoes"""
        print("\n[FECHANDO] Conexoes...")
        for cliente in self.clientes:
            try:
                cliente.close()
            except:
                pass
        self.socket_servidor.close()
        print("[OK] Servidor encerrado.\n")


def main():
    """Funcao principal do servidor"""
    print("\n" + "="*60)
    print("  SISTEMA DE MULTIPLICACAO DISTRIBUIDA DE MATRIZES")
    print("  Modo: SERVIDOR")
    print("="*60 + "\n")
    
    # Configuracoes
    HOST = 'localhost'
    PORT = 5000
    NUM_CLIENTES = 2
    
    # Dimensoes das matrizes
    M = 4  # Linhas de A
    N = 3  # Colunas de A / Linhas de B
    P = 2  # Colunas de B
    
    # Cria servidor
    servidor = ServidorMultiplicacao(HOST, PORT)
    
    try:
        # Inicia servidor
        servidor.iniciar_servidor()
        
        # Aceita clientes
        servidor.aceitar_clientes(NUM_CLIENTES)
        
        # Gera matrizes
        A, B = servidor.gerar_matrizes(M, N, P)
        
        print("\n[MATRIZ A]:")
        print(A)
        print("\n[MATRIZ B]:")
        print(B)
        
        # Executa multiplicacao distribuida
        C = servidor.multiplicar_distribuido(A, B)
        
        print("\n[MATRIZ RESULTADO C]:")
        print(C)
        
        # Verifica resultado
        servidor.verificar_resultado(A, B, C)
        
        # Demonstracao com matrizes maiores
        print("\n" + "="*60)
        print("[TESTE] Matrizes maiores")
        print("="*60)
        
        M2, N2, P2 = 100, 80, 60
        A2, B2 = servidor.gerar_matrizes(M2, N2, P2)
        C2 = servidor.multiplicar_distribuido(A2, B2)
        servidor.verificar_resultado(A2, B2, C2)
        
    except KeyboardInterrupt:
        print("\n\n[INTERROMPIDO] Pelo usuario")
    except Exception as e:
        print(f"\n[ERRO] {e}")
    finally:
        servidor.fechar_conexoes()


if __name__ == "__main__":
    main()