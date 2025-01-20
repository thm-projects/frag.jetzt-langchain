# frag.jetzt Langchain (AI Provider)

This service serves all AI related functions for the webapp frag.jetzt.
See [git.thm.de/arsnova/frag.jetzt](https://git.thm.de/arsnova/frag.jetzt) or [github.com/thm-projects/frag.jetzt](https://github.com/thm-projects/frag.jetzt).

## Installation

You need to use [git.thm.de/arsnova/frag.jetzt-docker-orchestration](https://git.thm.de/arsnova/frag.jetzt-docker-orchestration) to run this app either locally (`./run-local.sh`), with docker (`./run-docker.sh`) or manually (using `langchain serve`).

When you have [Poetry](https://python-poetry.org/docs/) installed, simply type `poetry install`.

Install `libmagic` (or `libmagic-dev`), if necessary.

To run all evaluations and tests, you need to install celadon **inside the train directory**.
See [here](https://github.com/Pleias/toxic-commons?tab=readme-ov-file#installation) for more information.

```shell
cd train
git clone https://huggingface.co/PleIAs/celadon
```

If you need to install LangChain CLI:

```bash
pip install -U langchain-cli
```

How you build docker image for local run (`./run-docker.sh`):

```shell
./build-local.sh
```
