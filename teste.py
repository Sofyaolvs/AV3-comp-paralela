
import subprocess
import time
import sys
import os

def limpar_tela():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def executar_teste():
    """Executa teste completo do sistema"""
    
    print("\n" + "="*70)
    print("  TESTE AUTOMATIZADO - MULTIPLICACAO DISTRIBUIDA DE MATRIZES")
    print("="*70 + "\n")
    
    print("[INFO] Este script ira:")
    print("   1. Iniciar o servidor em um processo")
    print("   2. Iniciar 2 clientes em processos separados")
    print("   3. Executar a multiplicacao distribuida")
    print("   4. Verificar os resultados")
    print("\n" + "="*70 + "\n")
    
    input("Pressione ENTER para iniciar o teste...")
    
    processos = []
    
    try:
        # Inicia servidor
        print("\n[SERVIDOR] Iniciando servidor...")
        servidor = subprocess.Popen(
            [sys.executable, 'servidor.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processos.append(('Servidor', servidor))
        time.sleep(2)
        
        # Inicia cliente 1
        print("[CLIENTE 1] Iniciando Cliente 1...")
        cliente1 = subprocess.Popen(
            [sys.executable, 'cliente.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processos.append(('Cliente 1', cliente1))
        time.sleep(1)
        
        # Inicia cliente 2
        print("[CLIENTE 2] Iniciando Cliente 2...")
        cliente2 = subprocess.Popen(
            [sys.executable, 'cliente.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processos.append(('Cliente 2', cliente2))
        
        print("\n[OK] Todos os processos iniciados!")
        print("[AGUARDANDO] Conclusao do teste...\n")
        print("="*70)
        
        # Aguarda servidor terminar (ele termina apos processar)
        servidor.wait(timeout=30)
        
        # Aguarda clientes
        cliente1.wait(timeout=5)
        cliente2.wait(timeout=5)
        
        print("\n" + "="*70)
        print("[SUCESSO] TESTE CONCLUIDO!")
        print("="*70 + "\n")
        
        # Mostra saidas
        print("\n[SAIDA] SERVIDOR:")
        print("-"*70)
        stdout, stderr = servidor.communicate()
        print(stdout)
        if stderr:
            print("Erros:", stderr)
        
        print("\n[SAIDA] CLIENTE 1:")
        print("-"*70)
        stdout, stderr = cliente1.communicate()
        print(stdout)
        if stderr:
            print("Erros:", stderr)
            
        print("\n[SAIDA] CLIENTE 2:")
        print("-"*70)
        stdout, stderr = cliente2.communicate()
        print(stdout)
        if stderr:
            print("Erros:", stderr)
        
    except subprocess.TimeoutExpired:
        print("\n[TIMEOUT] O teste demorou mais que o esperado")
        
    except KeyboardInterrupt:
        print("\n\n[INTERROMPIDO] Teste interrompido pelo usuario")
        
    except Exception as e:
        print(f"\n[ERRO] Durante o teste: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Encerra todos os processos
        print("\n[FECHANDO] Encerrando processos...")
        for nome, processo in processos:
            try:
                processo.terminate()
                processo.wait(timeout=2)
                print(f"   [OK] {nome} encerrado")
            except:
                processo.kill()
                print(f"   [FORCADO] {nome} foi forcado a encerrar")
                
        print("\n[OK] Teste finalizado.\n")


def menu_principal():
    """Menu principal do script de teste"""
    
    while True:
        limpar_tela()
        print("\n" + "="*70)
        print("  SISTEMA DE MULTIPLICACAO DISTRIBUIDA - MENU DE TESTES")
        print("="*70 + "\n")
        
        print("Escolha uma opcao:")
        print()
        print("1. Executar teste automatizado completo")
        print("2. Iniciar apenas o servidor")
        print("3. Iniciar apenas um cliente")
        print("4. Ver instrucoes de uso manual")
        print("5. Sair")
        print()
        
        opcao = input("Opcao: ").strip()
        
        if opcao == '1':
            executar_teste()
            input("\nPressione ENTER para voltar ao menu...")
            
        elif opcao == '2':
            print("\n[SERVIDOR] Iniciando servidor...")
            print("(Pressione Ctrl+C para interromper)\n")
            try:
                subprocess.run([sys.executable, 'servidor.py'])
            except KeyboardInterrupt:
                print("\n\n[INTERROMPIDO] Servidor interrompido")
            input("\nPressione ENTER para voltar ao menu...")
            
        elif opcao == '3':
            print("\n[CLIENTE] Iniciando cliente...")
            print("(Pressione Ctrl+C para interromper)\n")
            try:
                subprocess.run([sys.executable, 'cliente.py'])
            except KeyboardInterrupt:
                print("\n\n[INTERROMPIDO] Cliente interrompido")
            input("\nPressione ENTER para voltar ao menu...")
            
        elif opcao == '4':
            print("\n" + "="*70)
            print("  INSTRUCOES DE USO MANUAL")
            print("="*70 + "\n")
            print("Para executar o sistema manualmente, siga os passos:")
            print()
            print("1. Abra 3 terminais diferentes")
            print()
            print("2. No Terminal 1 (Servidor):")
            print("   $ python servidor.py")
            print()
            print("3. No Terminal 2 (Cliente 1):")
            print("   $ python cliente.py")
            print()
            print("4. No Terminal 3 (Cliente 2):")
            print("   $ python cliente.py")
            print()
            print("5. O servidor aguardara os 2 clientes conectarem")
            print("6. Apos conexao, a multiplicacao sera executada automaticamente")
            print()
            print("Para usar em maquinas diferentes:")
            print("   $ python cliente.py <IP_DO_SERVIDOR> 5000")
            print()
            print("="*70)
            input("\nPressione ENTER para voltar ao menu...")
            
        elif opcao == '5':
            print("\n[SAINDO] Encerrando...\n")
            break
            
        else:
            print("\n[ERRO] Opcao invalida!")
            time.sleep(1)


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n[SAINDO] Encerrando...\n")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()