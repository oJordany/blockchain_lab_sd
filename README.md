# LSD 2025 - Blockchain (Bitcoin-like)

## Integrantes
- Syanne Karroline Moreira Tavares
- Luiz Jordany de Sousa Silva
- Ivan Luis Gama Grana

## Visao geral (curta)
Este projeto implementa uma criptomoeda/transacao distribuida simplificada, seguindo os requisitos de `LSD 2025 - Blockchain.pdf` e o protocolo definido em `Padrao_blockchain.pdf`. Cada no roda como processo independente, mantem sua copia local da blockchain, propaga transacoes e blocos via sockets TCP com JSON e executa Proof of Work (hash iniciando com `000`).

## Requisitos atendidos (resumo)
- Processo independente por no, porta configuravel e bootstrap (`src/lsdchain/network/node.py`).
- Comunicacao via sockets TCP + JSON e mensagens padronizadas (`src/lsdchain/network/protocol.py`).
- Estrutura de transacoes, blocos, bloco genesis e hash SHA-256 (`src/lsdchain/core/transaction.py`, `src/lsdchain/core/block.py`).
- Proof of Work com dificuldade fixa `000` e recompensa de mineracao (coinbase = 50) (`src/lsdchain/core/mining.py`).
- Validacao de cadeia, consenso por cadeia mais longa e sincronizacao (`src/lsdchain/core/blockchain.py`, `src/lsdchain/network/node.py`).

## Como executar (Python)
1. Instale Python 3.11+ com Tkinter.
2. Dependencias:

```bash
pip install -r requirements.txt
```

3. Inicie um no (interface Tkinter):

```bash
python main.py
```

4. Se precisar modo texto (sem GUI):

```bash
python main.py --cli --host 127.0.0.1 --port 5000
```

5. Inicie outros nos com bootstrap (modo texto):

```bash
python main.py --cli --host 127.0.0.1 --port 5001 --bootstrap 127.0.0.1:5000
python main.py --cli --host 127.0.0.1 --port 5002 --bootstrap 127.0.0.1:5000
```

## Como executar (Docker)
Build e execucao com tres nos de exemplo (modo texto):

```bash
docker compose up --build
```

Cada service executa em modo texto (`--cli`). Interface Tkinter exige ambiente grafico local.

## Protocolo de comunicacao (Padrao_blockchain.pdf)
- Transmissao: `[4 bytes tamanho big-endian][JSON UTF-8]`.
- Estrutura de mensagem: `{ "type": "<TIPO>", "payload": { ... }, "sender": "host:port" }`.
- Tipos suportados: `NEW_TRANSACTION`, `NEW_BLOCK`, `REQUEST_CHAIN`, `RESPONSE_CHAIN` (`src/lsdchain/network/protocol.py`).

## Estruturas de dados
Transacao (obrigatorio): `id`, `origem`, `destino`, `valor`, `timestamp` (`src/lsdchain/core/transaction.py`).

Bloco (obrigatorio): `index`, `previous_hash`, `transactions`, `nonce`, `timestamp`, `hash` (`src/lsdchain/core/block.py`).

Bloco genesis (fixo): `index=0`, `previous_hash=0*64`, `timestamp=0`, `nonce=0`, `hash=816534...` (`src/lsdchain/core/block.py`).

Recompensa de mineracao: primeira transacao do bloco e coinbase (valor 50) (`src/lsdchain/core/mining.py`).

## Como funciona a blockchain (explicacao simples e detalhada)
- Uma **blockchain** e uma lista de blocos encadeados. Cada bloco guarda um conjunto de transacoes (`src/lsdchain/core/block.py`).
- Cada bloco contem o **hash** do bloco anterior. Isso cria um encadeamento: se alguem mudar um bloco antigo, o hash muda e a cadeia fica invalida (`src/lsdchain/core/blockchain.py`).
- O **Proof of Work** exige achar um `nonce` que gere um hash com prefixo `000`. Isso torna a criacao de blocos mais lenta e dificulta fraudes (`src/lsdchain/core/mining.py`).
- A rede aceita a **cadeia mais longa e valida**. Se um no entrar atrasado, ele pede a cadeia completa e troca se a nova for maior (`src/lsdchain/network/node.py`).
- A **transacao coinbase** (origem `coinbase`) da recompensa a quem minerou o bloco (`src/lsdchain/core/mining.py`).

Conceitos basicos (em linguagem simples):
- **Transacao**: e uma transferencia de valor entre duas partes. Ela so entra na blockchain depois que um bloco e minerado. Enquanto isso, fica no pool de pendentes (`src/lsdchain/core/transaction.py`, `src/lsdchain/core/blockchain.py`).
- **Bloco**: e um pacote de transacoes. Ele tem um hash proprio, e tambem o hash do bloco anterior, formando a cadeia (`src/lsdchain/core/block.py`).
- **Hash**: e uma impressao digital do bloco. Qualquer mudanca no bloco gera um hash diferente, por isso e facil detectar alteracoes (`src/lsdchain/core/block.py`).
- **Proof of Work**: e a prova de que o minerador gastou processamento procurando um `nonce` valido. Isso protege a rede contra alteracoes faceis (`src/lsdchain/core/mining.py`).
- **Consenso**: e a regra para decidir qual cadeia e aceita. Aqui, vence a cadeia valida com mais blocos (`src/lsdchain/core/blockchain.py`).

## Estrutura de pastas (e papel de cada componente)
- `main.py`: ponto de entrada que carrega a interface Tkinter (ou CLI com `--cli`).
- `src/lsdchain/cli/app.py`: menu em modo texto (opcional).
- `src/lsdchain/gui/app_tk.py`: interface Tkinter.
- `src/lsdchain/network/node.py`: no P2P, sockets, broadcast, sincronizacao.
- `src/lsdchain/network/protocol.py`: formato e tipos de mensagens.
- `src/lsdchain/core/blockchain.py`: validacao de cadeia, saldo e consenso.
- `src/lsdchain/core/block.py`: estrutura do bloco e calculo do hash.
- `src/lsdchain/core/transaction.py`: estrutura da transacao.
- `src/lsdchain/core/mining.py`: algoritmo de mineracao (PoW).
- `Dockerfile` e `docker-compose.yml`: empacotamento e execucao com Docker.

## Fluxo do sistema (passo a passo)
### 1) Inicializacao do no
1. O usuario executa `python main.py`.
2. `main.py` chama a interface Tkinter (`src/lsdchain/gui/app_tk.py`) ou o CLI com `--cli`.
3. A interface cria o no (`src/lsdchain/network/node.py`) e inicia o servidor TCP.
4. Se houver `--bootstrap`, o no envia `REQUEST_CHAIN` e sincroniza.

### 2) Criar transacao
1. A interface chama `_create_transaction` em `src/lsdchain/gui/app_tk.py` (ou `src/lsdchain/cli/app.py` no modo texto).
2. A transacao e criada em `src/lsdchain/core/transaction.py`.
3. `Node.broadcast_transaction` valida saldo em `src/lsdchain/core/blockchain.py`.
4. O no propaga `NEW_TRANSACTION` para os peers (`src/lsdchain/network/protocol.py`).

### 3) Minerar bloco
1. Menu chama `Node.mine` (`src/lsdchain/network/node.py`).
2. `Miner.mine_block` monta o bloco com coinbase e transacoes pendentes (`src/lsdchain/core/mining.py`).
3. O minerador tenta nonces ate gerar hash com `000` (`src/lsdchain/core/block.py`).
4. O bloco valido e adicionado localmente e propagado via `NEW_BLOCK`.

### 4) Receber bloco remoto
1. O no recebe `NEW_BLOCK` (`src/lsdchain/network/node.py`).
2. O bloco e validado (hash, PoW e transacoes) em `src/lsdchain/core/blockchain.py`.
3. Se valido, o bloco e adicionado e as transacoes pendentes sao removidas.

### 5) Sincronizar cadeia (no atrasado)
1. O no envia `REQUEST_CHAIN`.
2. O peer responde `RESPONSE_CHAIN` com `chain` e `pending_transactions`.
3. Se a nova cadeia for maior e valida, substitui a atual.

## Acoes disponiveis no menu
- Criar transacao.
- Ver transacoes pendentes.
- Minerar bloco.
- Ver blockchain.
- Ver saldo de um endereco.
- Ver peers conectados.
- Conectar manualmente a um peer.
- Sincronizar blockchain.

## Observacoes e limitacoes
- Nao ha servidor central.
- O consenso e baseado na cadeia mais longa valida.
- A validacao de saldo impede transacoes com saldo negativo.
- O protocolo segue o padrao de `Padrao_blockchain.pdf`.
