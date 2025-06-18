# temptracker

Apresentando Meu Projeto Incrível!

[![Construído com Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Licença: MIT

## Visão Geral do Projeto

`temptracker` é um sistema robusto de monitoramento de temperatura projetado para rastrear temperaturas ambientais e alertar os usuários quando os limites predefinidos são excedidos. Este aplicativo é construído com Django, utilizando um sistema de tarefas agendadas (APScheduler) para buscar periodicamente dados de temperatura da API Open-Meteo com base em locais e limites configurados. Quando um limite de temperatura é ultrapassado, um alerta por e-mail é enviado para o endereço de notificação especificado.

**Observação**: Este projeto atua como o backend da aplicação. O frontend correspondente está disponível no repositório [TempTrackerFrontEnd](https://github.com/AfonsoDglan/TempTrackerFrontEnd).

### Funcionalidades

* **Monitoramento de Temperatura**: Busca periodicamente dados de temperatura para locais geográficos especificados usando a API Open-Meteo.
* **Alertas Configuráveis**: Os usuários podem definir limites de temperatura e intervalos de monitoramento para cada local.
* **Notificações por E-mail**: Envia alertas automáticos por e-mail quando as temperaturas registradas excedem os limites definidos.
* **Confirmação de Alerta**: Fornece um endpoint de API para confirmar que um alerta foi lido.
* **Dados Históricos**: Armazena leituras de temperatura e alertas para referência e análise futuras.
* **Gerenciamento de Usuários**: Integra-se com `django-allauth` para autenticação segura de usuários, registro e gerenciamento, incluindo autenticação multifator (MFA).

### Arquitetura

`temptracker` é estruturado como um aplicativo Django, projetado para escalabilidade e fácil implantação usando Docker.

* **Core Django**: O principal framework web que lida com roteamento, ORM e lógica de negócios.
* **Django REST Framework**: Fornece endpoints de API para gerenciar configurações de monitoramento, leituras de temperatura e alertas.
* **APScheduler com DjangoJobStore**: Gerencia tarefas agendadas para consultar a API Open-Meteo para dados de temperatura. Cada instância de `MonitorSetting` pode ter seu próprio job agendado.
* **PostgreSQL**: O banco de dados relacional usado para armazenamento persistente de todos os dados do aplicativo, incluindo informações do usuário, configurações de monitoramento, leituras de temperatura e alertas.
* **Redis**: Usado para cache e, potencialmente, para enfileiramento de tarefas em uma configuração mais complexa.
* **API Open-Meteo**: Serviço externo usado para recuperar dados de temperatura em tempo real com base em latitude e longitude.
* **Backend de E-mail**: Configurado para enviar notificações por e-mail, usando Anymail para produção e um backend de console para desenvolvimento local.
    * **Configuração de E-mail**: Para o envio de e-mails, é necessário configurar as seguintes variáveis no arquivo `config/settings/base.py` (ou em variáveis de ambiente, que é a prática recomendada para produção):
        ```python
        EMAIL_HOST_USER = 'your_email@gmail.com' # Altere para o seu e-mail
        EMAIL_HOST_PASSWORD = 'your_app_password' # Altere para a sua chave de aplicativo/senha do e-mail: [help in](https://myaccount.google.com/apppasswords)
        DEFAULT_FROM_EMAIL = 'your_email@gmail.com' # Altere para o seu e-mail
        ```
* **Docker & Docker Compose**: Contêinerização para fácil configuração, desenvolvimento e implantação em diferentes ambientes (local, produção, documentação).
* **Traefik (Produção)**: Atua como um proxy reverso e terminador SSL na configuração do Docker de produção.
* **Esse projeto está configurado com a time zone: America/Sao_Paulo**: Caso estaja usando linux utilize o comando `timedatectl` para verificar se o seu sistema operacional está no meus UTC

## Comandos Básicos

Este projeto usa `Cookiecutter Django` como sua base, que fornece um layout de projeto bem estruturado e práticas de desenvolvimento comuns.

### Rodando o Projeto Localmente (Desenvolvimento)

Para rodar o projeto localmente em modo de desenvolvimento com Docker Compose, use o seguinte comando:

```bash
docker compose -f docker-compose.local.yml up -d --build
````

Isso irá construir as imagens (se necessário) e iniciar os serviços em segundo plano.

### Verificando os Logs do Serviço Django

Para visualizar os logs do serviço Django local, use:

```bash
docker logs temptracker_local_django
```

### Criando um Superusuário

Para criar uma conta de superusuário no ambiente de desenvolvimento local, use o seguinte comando:

```bash
docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser
```

Siga as instruções no terminal para definir o nome de usuário, e-mail e senha.

### Acessando a Área Administrativa

Após iniciar o projeto localmente e criar um superusuário, você pode acessar a área administrativa do Django em:

[http://localhost:8000/admin/](https://www.google.com/search?q=http://localhost:8000/admin/)


### Verificações de Tipo

Execute verificações de tipo usando `mypy` para garantir a consistência de tipo em todo o código-base:

```bash
$ mypy temptracker
```

### Cobertura de Testes

Para executar os testes, verificar sua cobertura de teste e gerar um relatório de cobertura HTML, use os seguintes comandos:

```bash
$coverage run -m pytest$ coverage html
$ open htmlcov/index.html
```

#### Executando testes com pytest

Para simplesmente executar os testes sem cobertura:

```bash
$ pytest
```

## Documentação

A documentação do projeto é construída usando Sphinx e pode ser gerada e servida localmente usando Docker.

### Construindo e Servindo a Documentação Localmente

Para construir e servir a documentação, use o seguinte comando Docker Compose:

```bash
docker compose -f docker-compose.docs.yml up docs
```

As alterações feitas nos arquivos no diretório `docs/` (por exemplo, `docs/howto.rst`, `docs/index.rst`, `docs/users.rst`) serão automaticamente detectadas e recarregadas. Sphinx é a ferramenta usada para construir a documentação.

### Docstrings para Documentação

A extensão `apidoc` para Sphinx é usada para gerar automaticamente documentação a partir do código usando assinaturas e docstrings. Ambos os estilos de docstring Numpy e Google são suportados e serão incluídos na documentação. Para um exemplo, consulte a fonte da página `users.rst`.

Para compilar automaticamente todas as docstrings em arquivos de origem de documentação, use o comando:

```bash
make apidocs
```

Este comando também pode ser executado dentro do contêiner Docker:

```bash
docker run --rm docs make apidocs
```

### Adicionando Novas Linguagens para Traduções

1.  Atualize a configuração `LANGUAGES` em `config/settings/base.py` para incluir a nova linguagem.

2.  Crie uma nova pasta de localidade (por exemplo, `fr_FR` para francês ou `pt_BR` para português do Brasil) ao lado de `temptracker/locale/`.

3.  Gere os arquivos Portable Object (`.po`) para a nova linguagem usando:

    ```bash
    docker compose -f docker-compose.local.yml run --rm django python manage.py makemessages --all --no-location
    ```

    Esses arquivos conterão strings traduzíveis com `msgid` e exigirão tradução como `msgstr`. Por exemplo: `msgid "users"` se torna `msgstr "utilisateurs"`.

4.  Uma vez que todas as traduções estejam completas, compile-as em arquivos Machine Object (`.mo`), que são usados pelo aplicativo:

    ```bash
    docker compose -f docker-compose.local.yml run --rm django python manage.py compilemessages
    ```

    Observe que os arquivos `.po` não são usados diretamente pelo aplicativo; apenas os arquivos `.mo` compilados são.

### Traduções em Produção

Em um ambiente de produção, a imagem Docker executa automaticamente `compilemessages` durante o tempo de construção. Portanto, desde que seus arquivos `.po` estejam atualizados, suas traduções serão refletidas no aplicativo implantado.

## Implantação

Instruções detalhadas de implantação para este aplicativo podem ser encontradas na [documentação do Docker do cookiecutter-django](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).

### Docker

O projeto usa Docker para conteinerização, com arquivos `docker-compose` separados para desenvolvimento local (`docker-compose.local.yml`) e produção (`docker-compose.production.yml`).

  * **Desenvolvimento Local**: `docker-compose.local.yml` define serviços como `django` e `postgres` para um ambiente de desenvolvimento local. Ele configura volumes para persistência de dados e mapeia portas para fácil acesso.
  * **Implantação em Produção**: `docker-compose.production.yml` inclui serviços para `django`, `postgres`, `traefik`, `redis` e `awscli`, configurados para um ambiente de produção com volumes persistentes e mapeamento de portas para acesso público.
