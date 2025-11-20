#!/usr/bin/env python3
"""
Servidor de Multiplicação de Matrizes Distribuída
Processa submatrizes recebidas do cliente usando multiprocessing
"""

import socket
import pickle
import numpy as np
from multiprocessing import Pool, cpu_count
import sys


def multiply_matrix_chunk(args):
    """
    Multiplica uma linha da matriz A pela matriz B completa
    Usada para paralelização com multiprocessing
    """
    row, matrix_b = args
    return np.dot(row, matrix_b)


def matrix_multiplication(submatrix_a, matrix_b, num_cores=2):
    """
    Realiza multiplicação de matrizes usando multiprocessing
    
    Args:
        submatrix_a: Submatriz de A para processar
        matrix_b: Matriz B completa
        num_cores: Número de cores para usar
    
    Returns:
        Resultado da multiplicação
    """
    # Prepara os argumentos para cada processo
    args = [(submatrix_a[i], matrix_b) for i in range(len(submatrix_a))]
    
    # Usa Pool para paralelizar a multiplicação
    with Pool(processes=num_cores) as pool:
        result_rows = pool.map(multiply_matrix_chunk, args)
    
    return np.array(result_rows)


def start_server(host='0.0.0.0', port=5000, num_cores=2):
    """
    Inicia o servidor para receber e processar submatrizes
    
    Args:
        host: Endereço IP para bind
        port: Porta para escutar
        num_cores: Número de cores CPU para usar
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"[OK] Servidor iniciado em {host}:{port}")
        print(f"Usando {num_cores} cores para processamento")
        print(f"CPU cores disponiveis: {cpu_count()}")
        print("Aguardando conexoes...\n")
        
        while True:
            client_socket, address = server_socket.accept()
            print(f"[+] Conexao aceita de {address}")
            
            try:
                # Recebe os dados do cliente
                data = b""
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    # Verifica se recebeu todos os dados (marcador de fim)
                    if b"END_OF_DATA" in chunk:
                        data = data.replace(b"END_OF_DATA", b"")
                        break
                
                # Deserializa os dados
                submatrix_a, matrix_b, chunk_id = pickle.loads(data)
                
                print(f"[<] Recebido chunk #{chunk_id}")
                print(f"   Submatriz A: {submatrix_a.shape}")
                print(f"   Matriz B: {matrix_b.shape}")

                # Realiza a multiplicação usando multiprocessing
                print(f"[*] Processando multiplicacao com {num_cores} cores...")
                result = matrix_multiplication(submatrix_a, matrix_b, num_cores)

                print(f"[OK] Resultado calculado: {result.shape}")
                
                # Serializa e envia o resultado
                result_data = pickle.dumps((result, chunk_id))
                client_socket.sendall(result_data + b"END_OF_DATA")

                print(f"[>] Resultado enviado para o cliente\n")

            except Exception as e:
                print(f"[X] Erro ao processar requisicao: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        print("\n[!] Servidor interrompido pelo usuario")
    except Exception as e:
        print(f"[X] Erro no servidor: {e}")
        import traceback
        traceback.print_exc()
    finally:
        server_socket.close()
        print("[X] Servidor encerrado")


if __name__ == "__main__":
    # Permite configurar porta e número de cores via linha de comando
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    num_cores = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    print("=" * 60)
    print("SERVIDOR DE MULTIPLICACAO DE MATRIZES DISTRIBUIDA")
    print("=" * 60)
    
    start_server(port=port, num_cores=num_cores)