# Contribuindo para o c_valor_intrinseco

Obrigado pelo interesse em contribuir! Este guia explica como participar do projeto.

## Como Contribuir

### 1. Reportar Bugs

- Abra uma Issue descrevendo o bug
- Inclua: versão do Python, sistema operacional, passos para reproduzir
- Se possível, inclua screenshots ou logs de erro

### 2. Sugerir Funcionalidades

- Abra uma Issue com a tag `enhancement`
- Descreva a funcionalidade desejada e seu caso de uso

### 3. Enviar Código

1. **Fork** o repositório
2. **Clone** seu fork:
   ```bash
   git clone https://github.com/SEU_USERNAME/c_valor_intrinseco.git
   cd c_valor_intrinseco
   ```
3. **Crie uma branch** para sua feature:
   ```bash
   git checkout -b feature/nome-da-feature
   ```
4. **Implemente** suas alterações
5. **Teste** localmente:
   ```bash
   python calculadora_gordon.py --bac
   python calculadora_gordon.py --ticker BAC
   streamlit run streamlit_app.py
   ```
6. **Commit** com mensagem descritiva:
   ```bash
   git commit -m "Adiciona modelo de dividendos decrescentes"
   ```
7. **Push** para seu fork:
   ```bash
   git push origin feature/nome-da-feature
   ```
8. Abra um **Pull Request**

## Diretrizes de Código

- **Estilo**: PEP 8 para Python
- **Nomes**: snake_case para funções/variáveis, UPPER_CASE para constantes
- **Comentários**: apenas quando necessário (código autoexplicativo)
- **Funções**: máximo 30 linhas quando possível
- **Docstrings**: incluir em funções públicas

## Estrutura de Commits

```
tipo(escopo): descrição

Exemplos:
feat(gordon): adiciona suporte a dividendos crescentes
fix(dcf): corrige cálculo do terminal value
docs(readme): atualiza exemplos de uso
refactor(ticker): melhora tratamento de erros
```

## Tipos de Commit

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `refactor`: Refatoração sem mudança de comportamento
- `test`: Adição de testes
- `chore`: Manutenção geral

## Perguntas?

Abra uma Issue com a tag `question` para qualquer dúvida.
