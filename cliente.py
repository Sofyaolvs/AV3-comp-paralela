#!/usr/bin/env python3

import socket
import pickle
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class DistributedMatrixClient:

    def __init__(self, servers):
        # Armazena a lista de servidores disponíveis para distribuir o trabalho
        self.servers = servers
        self.num_servers = len(servers)

    def send_to_server(self, server_info, submatrix_a, matrix_b, chunk_id):
        # Envia uma submatriz para um servidor e recebe o resultado processado
        # Processo: conecta ao servidor -> serializa e envia dados -> recebe resposta -> fecha conexão
        host, port = server_info

        try:
            # Tenta estabelecer conexão e processar a comunicação com o servidor
            # Cria o socket TCP e estabelece conexão com o servidor
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(60)

            print(f"[*] Conectando ao servidor {host}:{port} para chunk #{chunk_id}...")
            client_socket.connect((host, port))

            # Serializa os dados usando pickle e adiciona marcador de fim
            data = pickle.dumps((submatrix_a, matrix_b, chunk_id))
            client_socket.sendall(data + b"END_OF_DATA")
            print(f"[>] Dados enviados para {host}:{port} (chunk #{chunk_id})")

            # Recebe o resultado do servidor em blocos de 4KB
            result_data = b""
            while True:
                # Loop continua até receber todos os dados ou encontrar marcador de fim
                chunk = client_socket.recv(4096)
                if not chunk:
                    # Se não recebeu dados, encerra o loop
                    break
                result_data += chunk
                if b"END_OF_DATA" in chunk:
                    # Se encontrou o marcador de fim, remove e encerra o loop
                    result_data = result_data.replace(b"END_OF_DATA", b"")
                    break

            # Deserializa o resultado recebido
            result, received_chunk_id = pickle.loads(result_data)
            print(f"[<] Resultado recebido de {host}:{port} (chunk #{received_chunk_id})")

            client_socket.close()
            return (result, received_chunk_id)

        except Exception as e:
            # Captura erros de conexão, timeout ou falhas na comunicação
            print(f"[X] Erro ao comunicar com {host}:{port}: {e}")
            return None

    def multiply_distributed(self, matrix_a, matrix_b):
        # Coordena a multiplicação distribuída entre os servidores disponíveis
        print("\n" + "=" * 70)
        print(">>> INICIANDO MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
        print("=" * 70)

        # Valida se as dimensões são compatíveis para multiplicação (colunas de A = linhas de B)
        if matrix_a.shape[1] != matrix_b.shape[0]:
            raise ValueError("Dimensoes incompativeis para multiplicacao de matrizes")

        print(f"\nDimensoes:")
        print(f"   Matriz A: {matrix_a.shape}")
        print(f"   Matriz B: {matrix_b.shape}")
        print(f"   Resultado esperado: ({matrix_a.shape[0]}, {matrix_b.shape[1]})")
        print(f"\nServidores disponiveis: {self.num_servers}")

        # Divide a matriz A horizontalmente entre os servidores
        rows_per_server = matrix_a.shape[0] // self.num_servers
        submatrices = []

        for i in range(self.num_servers):
            # Itera sobre cada servidor para dividir a matriz A
            start_row = i * rows_per_server
            if i == self.num_servers - 1:
                # Último servidor processa as linhas restantes (caso não seja divisão exata)
                end_row = matrix_a.shape[0]
            else:
                # Demais servidores processam blocos iguais de linhas
                end_row = (i + 1) * rows_per_server

            submatrix = matrix_a[start_row:end_row]
            submatrices.append((submatrix, i))
            print(f"   Chunk #{i}: linhas {start_row} a {end_row-1} (shape: {submatrix.shape})")

        # Distribui as submatrizes para os servidores em paralelo usando threads
        print(f"\n[*] Distribuindo trabalho entre {self.num_servers} servidores...")
        start_time = time.time()

        results = {}
        with ThreadPoolExecutor(max_workers=self.num_servers) as executor:
            # Submete todas as tarefas para execução paralela
            future_to_chunk = {}
            for i, (submatrix, chunk_id) in enumerate(submatrices):
                # Para cada submatriz, submete uma tarefa ao executor
                server = self.servers[i]
                future = executor.submit(
                    self.send_to_server,
                    server,
                    submatrix,
                    matrix_b,
                    chunk_id
                )
                future_to_chunk[future] = chunk_id

            # Coleta os resultados conforme vão sendo completados
            for future in as_completed(future_to_chunk):
                # Aguarda cada tarefa completar e coleta o resultado
                result = future.result()
                if result:
                    # Se recebeu resultado válido, armazena no dicionário
                    partial_result, chunk_id = result
                    results[chunk_id] = partial_result

        # Ordena os resultados por chunk_id e concatena verticalmente
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
    # Gera matrizes aleatórias para testes com valores entre 1 e 9
    np.random.seed(seed)
    matrix_a = np.random.randint(1, 10, size=(m, n))
    matrix_b = np.random.randint(1, 10, size=(n, p))
    return matrix_a, matrix_b


def verify_result(matrix_a, matrix_b, result):
    # Verifica a corretude do resultado comparando com a multiplicação do numpy
    print("[*] Verificando correcao do resultado...")
    expected = np.dot(matrix_a, matrix_b)

    if np.allclose(result, expected):
        # Se os resultados são aproximadamente iguais (tolerância para erros de ponto flutuante)
        print("[OK] Resultado CORRETO! A multiplicacao distribuida funcionou perfeitamente.")
        return True
    else:
        # Se há diferenças significativas entre os resultados
        print("[X] Resultado INCORRETO! Ha diferencas no resultado.")
        print(f"Diferenca maxima: {np.max(np.abs(result - expected))}")
        return False


def get_matrix_dimensions():
    # Solicita ao usuário as dimensões das matrizes para multiplicação
    print("\nConfiguracao das dimensoes das matrizes:")
    print("   Matriz A: m x n")
    print("   Matriz B: n x p")
    print("   Resultado: m x p\n")

    # Obtém o número de linhas da matriz A
    while True:
        # Loop continua até obter um valor válido
        try:
            # Tenta converter a entrada para inteiro
            m = int(input("Digite o número de linhas de A (m): "))
            if m <= 0:
                # Valida se o valor é positivo
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            # Captura erro se a entrada não for um número válido
            print("[X] Digite um numero inteiro valido")

    # Obtém o número de colunas de A (que deve ser igual ao número de linhas de B)
    while True:
        # Loop continua até obter um valor válido
        try:
            # Tenta converter a entrada para inteiro
            n = int(input("Digite o número de colunas de A / linhas de B (n): "))
            if n <= 0:
                # Valida se o valor é positivo
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            # Captura erro se a entrada não for um número válido
            print("[X] Digite um numero inteiro valido")

    # Obtém o número de colunas da matriz B
    while True:
        # Loop continua até obter um valor válido
        try:
            # Tenta converter a entrada para inteiro
            p = int(input("Digite o número de colunas de B (p): "))
            if p <= 0:
                # Valida se o valor é positivo
                print("[X] O valor deve ser maior que 0")
                continue
            break
        except ValueError:
            # Captura erro se a entrada não for um número válido
            print("[X] Digite um numero inteiro valido")

    return m, n, p


def get_server_config():
    # Solicita ao usuário a configuração dos servidores (host e porta)
    print("\nConfiguracao dos servidores:")

    # Obtém a quantidade de servidores a serem utilizados
    while True:
        # Loop continua até obter um valor válido
        try:
            # Tenta converter a entrada para inteiro
            num_servers = int(input("Quantos servidores deseja usar? "))
            if num_servers <= 0:
                # Valida se o valor é positivo
                print("[X] O numero deve ser maior que 0")
                continue
            break
        except ValueError:
            # Captura erro se a entrada não for um número válido
            print("[X] Digite um numero inteiro valido")

    # Coleta informações de host e porta para cada servidor
    servers = []
    for i in range(num_servers):
        # Itera sobre o número de servidores para coletar configurações
        print(f"\n   Servidor {i+1}:")
        host = input(f"   Host (padrão: localhost): ").strip()
        if not host:
            # Se não digitou nada, usa localhost como padrão
            host = 'localhost'

        while True:
            # Loop continua até obter uma porta válida
            try:
                # Tenta converter a entrada para inteiro
                port_input = input(f"   Porta (padrão: {5000 + i}): ").strip()
                if not port_input:
                    # Se não digitou nada, usa porta sequencial (5000, 5001, ...)
                    port = 5000 + i
                else:
                    port = int(port_input)
                break
            except ValueError:
                # Captura erro se a entrada não for um número válido
                print("   [X] Digite um numero de porta valido")

        servers.append((host, port))

    return servers


def main():
    # Função principal que executa o cliente de multiplicação distribuída
    print("=" * 70)
    print("CLIENTE DE MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
    print("=" * 70)

    # Obtém a configuração dos servidores
    servers = get_server_config()

    print(f"\nConfiguracao final:")
    print(f"   Numero de servidores: {len(servers)}")
    for i, (host, port) in enumerate(servers, 1):
        print(f"   Servidor {i}: {host}:{port}")

    # Obtém as dimensões das matrizes
    m, n, p = get_matrix_dimensions()

    # Verifica se há servidores suficientes para as linhas da matriz
    if m < len(servers):
        # Alerta se o número de linhas for menor que o número de servidores
        print(f"\n[!] Aviso: O numero de linhas ({m}) e menor que o numero de servidores ({len(servers)})")
        print(f"   Algumas tarefas podem ficar vazias. Considere usar menos servidores.")

    print(f"\nGerando matrizes de teste:")
    print(f"   A: {m}x{n}")
    print(f"   B: {n}x{p}")

    matrix_a, matrix_b = generate_random_matrices(m, n, p)

    # Cria o cliente e executa a multiplicação distribuída
    client = DistributedMatrixClient(servers)

    try:
        # Tenta executar a multiplicação distribuída e exibir resultados
        result = client.multiply_distributed(matrix_a, matrix_b)

        # Exibe uma amostra do resultado
        rows_to_show = min(5, result.shape[0])
        cols_to_show = min(5, result.shape[1])
        print(f"Amostra do resultado (primeiros {rows_to_show}x{cols_to_show} elementos):")
        print(result[:rows_to_show, :cols_to_show])
        print()

        # Valida a corretude do resultado
        verify_result(matrix_a, matrix_b, result)

    except Exception as e:
        # Captura qualquer erro durante a execução e exibe detalhes
        print(f"\n[X] Erro durante a execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
