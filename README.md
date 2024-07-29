# PaperCast: AI generated podcast for each scientific research article

PaperCast is a project that turns any research articles into podcasts using AI generated audio. It is inspired by Illuminate <https://illuminate.withgoogle.com/> and ScienceCast <https://sciencecast.org/>.

> The author doesn't know any people working on Illuminate project nor their methods. The author is still in the waiting list for its beta release.

![image](papercast.png)

## Changelogs

* July 29th, 2024: refactorize arxiv reader and leverage its HTML render and parse to JSON + Markdown
* Jun 16th, 2024: add author interview mode, by adding "author_interview_prompt" in `prompt.yaml` and `additional_questions` provided by authors; add PDF mode so it can extract necessary information for any PDF paper from `pdfs` directory. Check `examples/run_cognitive.yaml` for example.
* Jun 15th, 2024: add subtitle `srt` file generation. See `examples/run_gorilla.yaml` to set `offset` if any intro audio, and example video at [PaperCast EP5: "Gorilla: Large Language Model Connected with Massive APIs"](https://www.youtube.com/watch?v=KH3SAbm14cI)

## Example

To generate a podcast for "Attention is all you need", you can simply run the following command:

```sh
python run.py examples/run_attention.yaml
```

It should produce `1706.03762.json` in the `transcript` directory and `1706.03762.wav` in the `audio` directory. 

Please also try a few example videos on Youtube. The play list link is at [here](https://www.youtube.com/watch?v=IpuUIDOfArY&list=PLdZH-mptYlBHSHV5Ij6AgRt577UlGKaGR)

[![Watch the video](https://img.youtube.com/vi/u6VHe1lJ94A/0.jpg)](https://youtu.be/u6VHe1lJ94A?si=7N3lT1akB1lAYLb8)


## Installation

Setup OpenAI API key

```sh
export OPENAI_API_KEY=sk-xxxx
```

Check out repo and put `ChatTTS` in the directory

```sh
git clone https://github.com/phunterlau/papercast
cd papercast/
git clone https://github.com/2noise/ChatTTS
cd ChatTTS
pip install -r requirements.txt
cd ..
pip install -r requirements.txt
```

Please note that `ChatTTS` is still very experimental. Please refer to its repo for issues and helps.

## How to build a podcast

Use `examples/run_attention.yaml` for example. It contains a few keys:

```YAML
url: "https://arxiv.org/abs/1706.03762"
use_cache: true
episode: 3
prompt: "dialogue_prompt"
background_knowledge: |
  Current year is 2024. Attention is all you need is known as the transformer paper published in 2017 by Google.
  It is the foundation paper of the current large language model research.
```

* `url`: an Arxiv URL (abs or pdf) or a local file path of a PDF file.
* `use_cache`: if load the cached LLM-generated transcript or start over.
* `episode` : Episode number.
* `prompt`: refer to `prompt.YAML` for the podcast style, dialogue or monologue etc.
* (optional) `background_knowledge`: additional knowledge for better context understanding. Use "None" if not available.
* (optional) `additional_questions`: additional research questions for input.

## How does it work

I prefer the podcast in the question answering style, so the transcript must include a smooth conversation for a general overview, a few interesting questions, and the discussion onto them. The process includes 3 steps

* predicting the research field of given article
* LLM role play as a senior researcher in the research field, ask a few questions.
* Generate a podcast by addressing these questions

## Limitations

* The question generation is limited to the article's title and abstract only. A better tree-level question generation using the full text might bring deeper and better questions.
* It depends on ChatTTS <https://github.com/2noise/ChatTTS> for audio generation. The features are still very experimental and the speaker voice lottery is very tricky.

## Future ideas

- [ ] more article readers beyond arxiv loader
- [x] a good PDF loader to parse article meta data and sections
- [ ] Add Chinese voices
- [x] Better question generation using full text
- [ ] Support multi-persons discussions with agentic workflow
- [x] Support different interview modes, e.g. host vs author

## License and disclaimer

This repo uses MIT License. It uses ChatTTS for audio generation and ChatTTS doesn't allow commercial use. The music in the podcast is generated by Suno.AI.

## Acknowledge

* Jina.ai has a good reader API <https://jina.ai/reader/>
* ChatTTS <https://github.com/2noise/ChatTTS>
