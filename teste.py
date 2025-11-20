#!/usr/bin/env python3
"""
Script de Teste Automatizado
Testa o sistema de multiplicação distribuída com diferentes cenários
"""

import subprocess
import time
import sys
import os
import tempfile


class TestRunner:
    def __init__(self):
        self.server_processes = []

    def start_servers(self):
        """Inicia os servidores em background"""
        print("="*60)
        print("Iniciando servidores para teste...")
        print("="*60)

        # Inicia servidor 1
        server1 = subprocess.Popen(
            ['python', 'servidor.py', '5000', '1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        self.server_processes.append(server1)
        print("✓ Servidor 1 iniciado (porta 5000)")

        # Inicia servidor 2
        server2 = subprocess.Popen(
            ['python', 'servidor.py', '5001', '2'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        self.server_processes.append(server2)
        print("✓ Servidor 2 iniciado (porta 5001)")

        # Aguarda servidores iniciarem
        print("\nAguardando servidores iniciarem...")
        time.sleep(3)
        print("✓ Servidores prontos!\n")

    def stop_servers(self):
        """Encerra todos os servidores"""
        print("\n" + "="*60)
        print("Encerrando servidores...")
        print("="*60)

        for proc in self.server_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()

        self.server_processes = []
        print("✓ Servidores encerrados\n")

    def run_test(self, test_name, rows_A, cols_A, cols_B):
        """Executa um teste específico"""
        print("="*60)
        print(f"TESTE: {test_name}")
        print("="*60)
        print(f"Dimensões: ({rows_A}x{cols_A}) × ({cols_A}x{cols_B})")
        print()

        # Cria script Python temporário para executar teste
        test_script = f"""
import numpy as np
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, r'{os.path.dirname(os.path.abspath(__file__))}')

from cliente import DistributedMatrixClient, verify_result

servers = [('localhost', 5000), ('localhost', 5001)]
client = DistributedMatrixClient(servers)

# Gera matrizes
np.random.seed(42)
matrix_A = np.random.randint(1, 10, size=({rows_A}, {cols_A}))
matrix_B = np.random.randint(1, 10, size=({cols_A}, {cols_B}))

print(f"Matriz A: {{matrix_A.shape}}")
print(f"Matriz B: {{matrix_B.shape}}")

# Executa multiplicação distribuída
try:
    result = client.multiply_distributed(matrix_A, matrix_B)

    if result is not None:
        # Verifica correção
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

        # Salva script temporário
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, 'test_matrix.py')

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)

        # Executa teste
        try:
            result = subprocess.run(
                ['python', test_file],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            print(result.stdout)

            if result.returncode == 0:
                print("✓ TESTE PASSOU!\n")
                return True
            else:
                print("✗ TESTE FALHOU!\n")
                if result.stderr:
                    print("Erros:", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("✗ TESTE TIMEOUT (>60s)\n")
            return False
        except Exception as e:
            print(f"✗ ERRO NO TESTE: {e}\n")
            return False

    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*10 + "SUITE DE TESTES AUTOMATIZADOS" + " "*18 + "║")
        print("║" + " "*10 + "Sistema de Multiplicação Distribuída" + " "*11 + "║")
        print("╚" + "="*58 + "╝")
        print()

        tests = [
            ("Matrizes Pequenas (10x10)", 10, 10, 10),
            ("Matrizes Médias (50x50)", 50, 50, 50),
            ("Matrizes Grandes (100x100)", 100, 100, 100),
            ("Matrizes Retangulares (80x120)", 80, 120, 60),
            ("Matrizes Retangulares (200x50)", 200, 50, 100),
            ("Matrizes Muito Grandes (1x3)", 1, 10, 10),
        ]

        results = []

        for test_name, rows_A, cols_A, cols_B in tests:
            success = self.run_test(test_name, rows_A, cols_A, cols_B)
            results.append((test_name, success))
            time.sleep(2)  # Pausa entre testes

        # Resumo
        print("\n")
        print("="*60)
        print("RESUMO DOS TESTES")
        print("="*60)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✓ PASSOU" if success else "✗ FALHOU"
            print(f"{status}: {test_name}")

        print()
        print(f"Total: {passed}/{total} testes passaram")

        if passed == total:
            print("="*60)
            print("🎉 TODOS OS TESTES PASSARAM! 🎉")
            print("="*60)
        else:
            print("="*60)
            print(f"⚠️  {total - passed} TESTE(S) FALHARAM")
            print("="*60)

        return passed == total


def main():
    runner = TestRunner()

    try:
        # Inicia servidores
        runner.start_servers()

        # Executa testes
        all_passed = runner.run_all_tests()

        # Encerra servidores
        runner.stop_servers()

        # Exit code
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuário")
        runner.stop_servers()
        sys.exit(1)
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        runner.stop_servers()
        sys.exit(1)


if __name__ == "__main__":
    main()
