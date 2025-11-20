import socket
import pickle
import numpy as np
from multiprocessing import Pool, cpu_count
import sys


def multiply_matrix_chunk(args):
    # Multiplica uma linha da matriz A pela matriz B completa
    row, matrix_b = args
    return np.dot(row, matrix_b)


def matrix_multiplication(submatrix_a, matrix_b, num_cores=2):
    # Realiza a multiplicação de matrizes usando multiprocessing para paralelizar o cálculo
    # Cada linha da submatriz A é processada por um processo separado
    args = [(submatrix_a[i], matrix_b) for i in range(len(submatrix_a))]

    # Cria um pool de processos para executar as multiplicações em paralelo
    with Pool(processes=num_cores) as pool:
        result_rows = pool.map(multiply_matrix_chunk, args)

    return np.array(result_rows)


def start_server(host='0.0.0.0', port=5000, num_cores=2):
    # Inicializa o servidor para receber e processar requisições de multiplicação
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Tenta inicializar o servidor e processar requisições
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"[OK] Servidor iniciado em {host}:{port}")
        print(f"Usando {num_cores} cores para processamento")
        print(f"CPU cores disponiveis: {cpu_count()}")
        print("Aguardando conexoes...\n")

        # Loop principal que aceita conexões continuamente
        while True:
            # Loop infinito aguardando novas conexões de clientes
            client_socket, address = server_socket.accept()
            print(f"[+] Conexao aceita de {address}")

            try:
                # Tenta processar a requisição do cliente
                # Recebe os dados enviados pelo cliente até encontrar o marcador de fim
                data = b""
                while True:
                    # Loop continua até receber todos os dados
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        # Se não recebeu dados, encerra o loop
                        break
                    data += chunk
                    if b"END_OF_DATA" in chunk:
                        # Se encontrou o marcador de fim, remove e encerra o loop
                        data = data.replace(b"END_OF_DATA", b"")
                        break

                # Deserializa os dados recebidos (submatriz A, matriz B e ID do chunk)
                submatrix_a, matrix_b, chunk_id = pickle.loads(data)

                print(f"[<] Recebido chunk #{chunk_id}")
                print(f"   Submatriz A: {submatrix_a.shape}")
                print(f"   Matriz B: {matrix_b.shape}")

                # Processa a multiplicação usando os cores disponíveis
                print(f"[*] Processando multiplicacao com {num_cores} cores...")
                result = matrix_multiplication(submatrix_a, matrix_b, num_cores)

                print(f"[OK] Resultado calculado: {result.shape}")

                # Serializa e envia o resultado de volta ao cliente
                result_data = pickle.dumps((result, chunk_id))
                client_socket.sendall(result_data + b"END_OF_DATA")

                print(f"[>] Resultado enviado para o cliente\n")

            except Exception as e:
                # Captura erros durante o processamento da requisição
                print(f"[X] Erro ao processar requisicao: {e}")
                import traceback
                traceback.print_exc()

            finally:
                # Sempre fecha a conexão com o cliente ao final
                client_socket.close()

    except KeyboardInterrupt:
        # Captura interrupção por Ctrl+C
        print("\n[!] Servidor interrompido pelo usuario")
    except Exception as e:
        # Captura outros erros no servidor
        print(f"[X] Erro no servidor: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Sempre fecha o socket do servidor ao encerrar
        server_socket.close()
        print("[X] Servidor encerrado")


if __name__ == "__main__":
    # Obtém porta e número de cores dos argumentos da linha de comando
    # Uso: python servidor.py [porta] [num_cores]
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    num_cores = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    print("=" * 60)
    print("SERVIDOR DE MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
    print("=" * 60)

    start_server(port=port, num_cores=num_cores)
