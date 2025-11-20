#!/usr/bin/env python3
"""
Cliente de Multiplicação de Matrizes Distribuída
Divide a carga de trabalho e distribui entre múltiplos servidores
"""

import socket
import pickle
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class DistributedMatrixClient:
    """
    Cliente para coordenar multiplicação de matrizes distribuída
    """
    
    def __init__(self, servers):
        """
        Args:
            servers: Lista de tuplas (host, port) dos servidores disponíveis
        """
        self.servers = servers
        self.num_servers = len(servers)
        
    def send_to_server(self, server_info, submatrix_a, matrix_b, chunk_id):
        """
        Envia uma submatriz para um servidor e recebe o resultado
        
        Args:
            server_info: Tupla (host, port) do servidor
            submatrix_a: Submatriz de A para processar
            matrix_b: Matriz B completa
            chunk_id: Identificador do chunk
        
        Returns:
            Tupla (resultado, chunk_id) ou None em caso de erro
        """
        host, port = server_info
        
        try:
            # Cria conexão com o servidor
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(60)  # Timeout de 60 segundos
            
            print(f"[*] Conectando ao servidor {host}:{port} para chunk #{chunk_id}...")
            client_socket.connect((host, port))
            
            # Serializa e envia os dados
            data = pickle.dumps((submatrix_a, matrix_b, chunk_id))
            client_socket.sendall(data + b"END_OF_DATA")
            print(f"[>] Dados enviados para {host}:{port} (chunk #{chunk_id})")
            
            # Recebe o resultado
            result_data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                result_data += chunk
                if b"END_OF_DATA" in chunk:
                    result_data = result_data.replace(b"END_OF_DATA", b"")
                    break
            
            # Deserializa o resultado
            result, received_chunk_id = pickle.loads(result_data)
            print(f"[<] Resultado recebido de {host}:{port} (chunk #{received_chunk_id})")
            
            client_socket.close()
            return (result, received_chunk_id)
            
        except Exception as e:
            print(f"[X] Erro ao comunicar com {host}:{port}: {e}")
            return None
    
    def multiply_distributed(self, matrix_a, matrix_b):
        """
        Realiza multiplicação de matrizes de forma distribuída
        
        Args:
            matrix_a: Matriz A (m x n)
            matrix_b: Matriz B (n x p)
        
        Returns:
            Matriz resultante C (m x p)
        """
        print("\n" + "=" * 70)
        print(">>> INICIANDO MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
        print("=" * 70)
        
        # Validação das dimensões
        if matrix_a.shape[1] != matrix_b.shape[0]:
            raise ValueError("Dimensões incompatíveis para multiplicação de matrizes")
        
        print(f"\nDimensoes:")
        print(f"   Matriz A: {matrix_a.shape}")
        print(f"   Matriz B: {matrix_b.shape}")
        print(f"   Resultado esperado: ({matrix_a.shape[0]}, {matrix_b.shape[1]})")
        print(f"\nServidores disponiveis: {self.num_servers}")
        
        # Divide a matriz A em submatrizes
        rows_per_server = matrix_a.shape[0] // self.num_servers
        submatrices = []
        
        for i in range(self.num_servers):
            start_row = i * rows_per_server
            if i == self.num_servers - 1:
                # Última submatriz pega o resto das linhas
                end_row = matrix_a.shape[0]
            else:
                end_row = (i + 1) * rows_per_server
            
            submatrix = matrix_a[start_row:end_row]
            submatrices.append((submatrix, i))
            print(f"   Chunk #{i}: linhas {start_row} a {end_row-1} (shape: {submatrix.shape})")
        
        # Envia as submatrizes para os servidores em paralelo
        print(f"\n[*] Distribuindo trabalho entre {self.num_servers} servidores...")
        start_time = time.time()
        
        results = {}
        with ThreadPoolExecutor(max_workers=self.num_servers) as executor:
            # Submete as tarefas
            future_to_chunk = {}
            for i, (submatrix, chunk_id) in enumerate(submatrices):
                server = self.servers[i]
                future = executor.submit(
                    self.send_to_server,
                    server,
                    submatrix,
                    matrix_b,
                    chunk_id
                )
                future_to_chunk[future] = chunk_id
            
            # Coleta os resultados
            for future in as_completed(future_to_chunk):
                result = future.result()
                if result:
                    partial_result, chunk_id = result
                    results[chunk_id] = partial_result
        
        # Ordena e concatena os resultados
        print(f"\n[*] Montando matriz final...")
        sorted_results = [results[i] for i in sorted(results.keys())]
        final_result = np.vstack(sorted_results)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\n[OK] MULTIPLICACAO CONCLUIDA!")
        print(f"Tempo total: {elapsed_time:.4f} segundos")
        print(f"Matriz resultante: {final_result.shape}")
        print("=" * 70 + "\n")
        
        return final_result


def generate_random_matrices(m, n, p, seed=42):
    """
    Gera matrizes aleatórias para teste
    
    Args:
        m: Número de linhas de A
        n: Número de colunas de A / linhas de B
        p: Número de colunas de B
        seed: Seed para reprodutibilidade
    
    Returns:
        Tupla (matrix_a, matrix_b)
    """
    np.random.seed(seed)
    matrix_a = np.random.randint(1, 10, size=(m, n))
    matrix_b = np.random.randint(1, 10, size=(n, p))
    return matrix_a, matrix_b


def verify_result(matrix_a, matrix_b, result):
    """
    Verifica se o resultado da multiplicação distribuída está correto
    """
    print("[*] Verificando correcao do resultado...")
    expected = np.dot(matrix_a, matrix_b)

    if np.allclose(result, expected):
        print("[OK] Resultado CORRETO! A multiplicacao distribuida funcionou perfeitamente.")
        return True
    else:
        print("[X] Resultado INCORRETO! Ha diferencas no resultado.")
        print(f"Diferenca maxima: {np.max(np.abs(result - expected))}")
        return False


def get_matrix_dimensions():
    """
    Solicita ao usuário as dimensões das matrizes

    Returns:
        Tupla (m, n, p) com as dimensões
    """
    print("\nConfiguracao das dimensoes das matrizes:")
    print("   Matriz A: m x n")
    print("   Matriz B: n x p")
    print("   Resultado: m x p\n")

    while True:
        try:
            m = int(input("Digite o número de linhas de A (m): "))
            if m <= 0:
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            print("[X] Digite um numero inteiro valido")

    while True:
        try:
            n = int(input("Digite o número de colunas de A / linhas de B (n): "))
            if n <= 0:
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            print("[X] Digite um numero inteiro valido")

    while True:
        try:
            p = int(input("Digite o número de colunas de B (p): "))
            if p <= 0:
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            print("[X] Digite um numero inteiro valido")

    return m, n, p


def get_server_config():
    """
    Solicita ao usuário a configuração dos servidores

    Returns:
        Lista de tuplas (host, port)
    """
    print("\nConfiguracao dos servidores:")

    while True:
        try:
            num_servers = int(input("Quantos servidores deseja usar? "))
            if num_servers <= 0:
                print("[X] O numero deve ser maior que 0")
                continue
            break
        except ValueError:
            print("[X] Digite um numero inteiro valido")

    servers = []
    for i in range(num_servers):
        print(f"\n   Servidor {i+1}:")
        host = input(f"   Host (padrão: localhost): ").strip()
        if not host:
            host = 'localhost'

        while True:
            try:
                port_input = input(f"   Porta (padrão: {5000 + i}): ").strip()
                if not port_input:
                    port = 5000 + i
                else:
                    port = int(port_input)
                break
            except ValueError:
                print("   [X] Digite um numero de porta valido")

        servers.append((host, port))

    return servers


def main():
    """
    Função principal do cliente
    """
    print("=" * 70)
    print("CLIENTE DE MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
    print("=" * 70)

    # Configuração dos servidores
    servers = get_server_config()

    print(f"\nConfiguracao final:")
    print(f"   Numero de servidores: {len(servers)}")
    for i, (host, port) in enumerate(servers, 1):
        print(f"   Servidor {i}: {host}:{port}")

    # Obtém dimensões das matrizes do usuário
    m, n, p = get_matrix_dimensions()

    # Verifica se o número de linhas é divisível pelo número de servidores
    if m < len(servers):
        print(f"\n[!] Aviso: O numero de linhas ({m}) e menor que o numero de servidores ({len(servers)})")
        print(f"   Algumas tarefas podem ficar vazias. Considere usar menos servidores.")

    print(f"\nGerando matrizes de teste:")
    print(f"   A: {m}x{n}")
    print(f"   B: {n}x{p}")

    matrix_a, matrix_b = generate_random_matrices(m, n, p)

    # Cria o cliente e realiza a multiplicação distribuída
    client = DistributedMatrixClient(servers)

    try:
        result = client.multiply_distributed(matrix_a, matrix_b)

        # Exibe uma amostra do resultado
        rows_to_show = min(5, result.shape[0])
        cols_to_show = min(5, result.shape[1])
        print(f"Amostra do resultado (primeiros {rows_to_show}x{cols_to_show} elementos):")
        print(result[:rows_to_show, :cols_to_show])
        print()

        # Verifica a correção
        verify_result(matrix_a, matrix_b, result)

    except Exception as e:
        print(f"\n[X] Erro durante a execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()