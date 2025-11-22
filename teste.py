#!/usr/bin/env python3

import subprocess
import time
import sys
import os
import tempfile


class TestRunner:
    def __init__(self):
        self.server_processes = []

    def start_servers(self):
        # Inicia múltiplos servidores em modo background para execução dos testes
        print("="*60)
        print("Iniciando servidores para teste...")
        print("="*60)

        # Inicia o primeiro servidor na porta 5000 com 1 core
        server1 = subprocess.Popen(
            ['python', 'servidor.py', '5000', '1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        self.server_processes.append(server1)
        print("Servidor 1 iniciado (porta 5000)")

        # Inicia o segundo servidor na porta 5001 com 2 cores
        server2 = subprocess.Popen(
            ['python', 'servidor.py', '5001', '2'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        self.server_processes.append(server2)
        print("Servidor 2 iniciado (porta 5001)")

        # Aguarda os servidores inicializarem completamente
        print("\nAguardando servidores iniciarem...")
        time.sleep(3)
        print("Servidores prontos!\n")

    def stop_servers(self):
        # Encerra todos os processos de servidor
        print("\n" + "="*60)
        print("Encerrando servidores...")
        print("="*60)

        for proc in self.server_processes:
            # Itera sobre cada processo de servidor para encerrá-lo
            try:
                # Tenta encerrar o processo graciosamente
                proc.terminate()
                proc.wait(timeout=5)
            except:
                # Se não responder, força o encerramento
                proc.kill()

        self.server_processes = []
        print("Servidores encerrados\n")

    def run_test(self, test_name, rows_A, cols_A, cols_B):
        # Executa um teste individual com as dimensões especificadas
        print("="*60)
        print(f"TESTE: {test_name}")
        print("="*60)
        print(f"Dimensões: ({rows_A}x{cols_A}) × ({cols_A}x{cols_B})")
        print()

        # Cria um script Python temporário para executar o teste
        test_script = f"""
import numpy as np
import sys
import os

# Adiciona o diretório do projeto ao path para importação
sys.path.insert(0, r'{os.path.dirname(os.path.abspath(__file__))}')

from cliente import DistributedMatrixClient, verify_result

# Configura os servidores de teste
servers = [('localhost', 5000), ('localhost', 5001)]
client = DistributedMatrixClient(servers)

# Gera matrizes aleatórias com seed fixa para reprodutibilidade
np.random.seed(42)
matrix_A = np.random.randint(1, 10, size=({rows_A}, {cols_A}))
matrix_B = np.random.randint(1, 10, size=({cols_A}, {cols_B}))

print(f"Matriz A: {{matrix_A.shape}}")
print(f"Matriz B: {{matrix_B.shape}}")

# Executa a multiplicação distribuída e valida o resultado
try:
    result = client.multiply_distributed(matrix_A, matrix_B)

    if result is not None:
        # Verifica se o resultado está correto
        is_correct = verify_result(matrix_A, matrix_B, result)

        print()
        print("="*60)
        print("RESULTADO DO TESTE")
        print("="*60)
        print(f"Resultado correto: {{'SIM' if is_correct else 'NAO'}}")
        print("="*60)

        if is_correct:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("ERRO: Falha na multiplicação distribuída")
        sys.exit(1)
except Exception as e:
    print(f"ERRO: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        # Salva o script em um arquivo temporário
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, 'test_matrix.py')

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)

        # Executa o teste e captura a saída
        try:
            # Tenta executar o script de teste
            result = subprocess.run(
                ['python', test_file],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            print(result.stdout)

            # Verifica o código de retorno para determinar sucesso ou falha
            if result.returncode == 0:
                # Código 0 indica sucesso
                print("TESTE PASSOU!\n")
                return True
            else:
                # Código diferente de 0 indica falha
                print("TESTE FALHOU!\n")
                if result.stderr:
                    # Se houver mensagens de erro, exibe
                    print("Erros:", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            # Captura erro se o teste demorar mais de 60 segundos
            print("TESTE TIMEOUT (>60s)\n")
            return False
        except Exception as e:
            # Captura outros erros durante a execução do teste
            print(f"ERRO NO TESTE: {e}\n")
            return False

    def run_all_tests(self):
        # Executa a suite completa de testes com diferentes tamanhos de matrizes
        print("\n")
        print("="*60)
        print("SUITE DE TESTES AUTOMATIZADOS")
        print("Sistema de Multiplicacao Distribuida")
        print("="*60)
        print()

        # Define os casos de teste com diferentes dimensões
        tests = [
            ("Matrizes Pequenas (10x10)", 10, 10, 10),
            ("Matrizes Médias (50x50)", 50, 50, 50),
            ("Matrizes Grandes (100x100)", 100, 100, 100),
            ("Matrizes Retangulares (80x120)", 80, 120, 60),
            ("Matrizes Retangulares (200x50)", 200, 50, 100),
            ("Matrizes Muito Grandes (1x3)", 20000, 20000, 2000),
        ]

        results = []

        # Executa cada teste sequencialmente
        for test_name, rows_A, cols_A, cols_B in tests:
            # Itera sobre cada caso de teste
            success = self.run_test(test_name, rows_A, cols_A, cols_B)
            results.append((test_name, success))
            time.sleep(2)

        # Gera o resumo dos resultados
        print("\n")
        print("="*60)
        print("RESUMO DOS TESTES")
        print("="*60)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            # Itera sobre os resultados para exibir o status de cada teste
            status = "PASSOU" if success else "FALHOU"
            print(f"{status}: {test_name}")

        print()
        print(f"Total: {passed}/{total} testes passaram")

        if passed == total:
            # Se todos os testes passaram
            print("="*60)
            print("TODOS OS TESTES PASSARAM!")
            print("="*60)
        else:
            # Se algum teste falhou
            print("="*60)
            print(f"{total - passed} TESTE(S) FALHARAM")
            print("="*60)

        return passed == total


def main():
    # Função principal que coordena a execução dos testes
    runner = TestRunner()

    try:
        # Tenta executar toda a suite de testes
        # Inicializa os servidores
        runner.start_servers()

        # Executa todos os testes
        all_passed = runner.run_all_tests()

        # Finaliza os servidores
        runner.stop_servers()

        # Retorna código de saída apropriado
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        # Captura interrupção por Ctrl+C
        print("\n\nTestes interrompidos pelo usuario")
        runner.stop_servers()
        sys.exit(1)
    except Exception as e:
        # Captura outros erros durante a execução dos testes
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        runner.stop_servers()
        sys.exit(1)


if __name__ == "__main__":
    main()
