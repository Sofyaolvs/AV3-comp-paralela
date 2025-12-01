# Sistema de Multiplicação de Matrizes Distribuída

Sistema de multiplicação de matrizes usando computação distribuída e paralela.

## Arquitetura

O sistema possui três componentes principais:

- **servidor.py** - Servidor que recebe submatrizes e processa usando multiprocessing
- **cliente.py** - Cliente que divide matrizes e distribui trabalho entre servidores
- **teste.py** - Suite de testes automatizados

## Como Funciona

### Servidor
- Recebe submatrizes via socket TCP
- Usa multiprocessing para paralelizar multiplicação linha por linha
- Retorna resultado processado ao cliente

### Cliente
- Divide matriz A em partes iguais entre servidores disponíveis
- Envia submatrizes em paralelo usando threads
- Coleta e concatena resultados na ordem correta

### Processamento
1. Cliente divide matriz A horizontalmente
2. Cada servidor recebe parte das linhas de A e matriz B completa
3. Servidores multiplicam usando Pool de processos
4. Cliente monta resultado final

## Uso

### Método Rápido (Recomendado)

Use os scripts fornecidos para iniciar/parar servidores automaticamente:

```bash
# Iniciar 2 servidores com 2 cores cada (padrão)
./iniciar_servidores.sh

# Ou especifique número de servidores e cores
./iniciar_servidores.sh 3 4  # 3 servidores com 4 cores cada
```

Em outro terminal:
```bash
# Executar cliente
python3 cliente.py
```

Para parar os servidores:
```bash
./parar_servidores.sh
```

### Método Manual

#### Iniciar Servidor

```bash
python3 servidor.py [porta] [num_cores]
```

Exemplos:
```bash
python3 servidor.py 5000 2
python3 servidor.py 5001 4
```

#### Executar Cliente

```bash
python3 cliente.py
```

O cliente irá solicitar:
- Número de servidores
- Host e porta de cada servidor
- Dimensões das matrizes (m, n, p)

**IMPORTANTE**: O cliente agora executa DUAS multiplicações:
1. **Multiplicação Serial** - Execução local para comparação
2. **Multiplicação Paralela Distribuída** - Usando os servidores

Ao final, exibe uma comparação de performance mostrando speedup ou slowdown.

### Executar Testes

```bash
python teste.py
```

Executa 6 testes automatizados com diferentes tamanhos de matrizes.

## Requisitos

```
numpy
python 3.x
```

## Exemplo de Execução

### Usando Scripts Automáticos

Terminal 1:
```bash
./iniciar_servidores.sh 2 2
```

Terminal 2:
```bash
python3 cliente.py
```

Configuração no cliente:
```
Quantos servidores: 2
Servidor 1 - Host: localhost, Porta: 5000
Servidor 2 - Host: localhost, Porta: 5001
Dimensões: m=100, n=50, p=80
```

Saída esperada:
```
EXECUTANDO MULTIPLICACAO SERIAL PARA COMPARACAO
[OK] MULTIPLICACAO SERIAL CONCLUIDA!
Tempo total: 0.1234 segundos

EXECUTANDO MULTIPLICACAO DISTRIBUIDA (PARALELA)
[*] Verificando conectividade dos servidores...
   [OK] Servidor localhost:5000 esta acessivel
   [OK] Servidor localhost:5001 esta acessivel
[OK] MULTIPLICACAO CONCLUIDA!
Tempo total: 0.0856 segundos

COMPARACAO DE PERFORMANCE: SERIAL vs PARALELO
Tempo Serial:    0.1234 segundos
Tempo Paralelo:  0.0856 segundos
Speedup:         1.44x
Melhoria:        30.63% mais rapido
[OK] A execucao paralela foi MAIS RAPIDA!
```

### Método Manual

Terminal 1:
```bash
python3 servidor.py 5000 2
```

Terminal 2:
```bash
python3 servidor.py 5001 2
```

Terminal 3:
```bash
python3 cliente.py
```

## Comunicação

- Protocolo: TCP Sockets
- Serialização: pickle
- Marcador de fim: END_OF_DATA

## Paralelização

- Cliente: ThreadPoolExecutor para envios simultâneos
- Servidor: multiprocessing.Pool para multiplicação de linhas

## Validação

O sistema valida automaticamente os resultados comparando com numpy.dot().



### Comparação Serial vs Paralelo
- O cliente agora executa automaticamente tanto a multiplicação serial quanto a paralela
- Exibe comparação de performance com:
  - Tempo de execução de cada método
  - Speedup (quantas vezes mais rápido)
  - Percentual de melhoria ou degradação

### Verificação de Conectividade
- Antes de processar, o cliente verifica se os servidores estão acessíveis
- Exibe mensagem clara se algum servidor estiver offline
- Evita timeout desnecessários

### Tratamento de Erros Melhorado
- Mensagens de erro mais descritivas
- Validação se há pelo menos um servidor disponível
- Tratamento adequado quando nenhum resultado é recebido

### Scripts de Automação
- `iniciar_servidores.sh` - Inicia múltiplos servidores automaticamente
- `parar_servidores.sh` - Finaliza todos os servidores em execução

## Solução de Problemas

### Erro: "timed out"
**Causa**: Servidores não estão rodando ou não são acessíveis.

**Solução**:
1. Certifique-se de iniciar os servidores antes do cliente
2. Use o script: `./iniciar_servidores.sh`
3. Ou inicie manualmente: `python3 servidor.py 5000 2`

### Erro: "need at least one array to concatenate"
**Causa**: Nenhum servidor retornou resultado (todos falharam).

**Solução**: Este erro foi corrigido. Agora o sistema:
1. Verifica conectividade antes de processar
2. Exibe mensagem clara se nenhum servidor está disponível
3. Não tenta concatenar arrays vazios
