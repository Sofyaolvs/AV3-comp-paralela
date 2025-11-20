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

### Iniciar Servidor

```bash
python servidor.py [porta] [num_cores]
```

Exemplos:
```bash
python servidor.py 5000 2
python servidor.py 5001 4
```

### Executar Cliente

```bash
python cliente.py
```

O cliente irá solicitar:
- Número de servidores
- Host e porta de cada servidor
- Dimensões das matrizes (m, n, p)

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

Terminal 1:
```bash
python servidor.py 5000 2
```

Terminal 2:
```bash
python servidor.py 5001 2
```

Terminal 3:
```bash
python cliente.py
```

Configuração no cliente:
```
Quantos servidores: 2
Servidor 1 - Host: localhost, Porta: 5000
Servidor 2 - Host: localhost, Porta: 5001
Dimensões: m=100, n=50, p=80
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
