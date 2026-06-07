# Field Notes: Building a Town of Tiny Minds

The starting point for Smol Town was a simple inversion of the usual AI story.
Big labs need a datacenter to run one mind. The Build Small Hackathon set a very
different constraint: use small models, with a maximum of 32 billion parameters
per model.

Instead of treating that as something to work around, I asked what becomes
possible *because* the models are small. The answer was a crowd.

If one model can play one character, then a collection of small-model agents can
become a whole place. That led to Smol Town: seven villagers living in Tinbury,
waking into a scandal, and improvising an unscripted soap opera.

## Casting for Conflict

The basic unit of the town is deliberately small. Each villager is a persona, a
private secret, and a set of feelings about the other villagers.

Mayor Doreen is pompous and image-conscious, but she also secretly drained the
town treasury to pay for a marble fountain. Marigold, the sharp-tongued florist,
still loves her blacksmith ex, Bram, and would rather die than admit it. Bram has
kept every letter she ever wrote him. Finn quietly loves Marigold. Pip knows far
too much about everybody.

The opening event says that the fountain fund is gone and Old Tom has named the
person responsible. Secrets plus relationships plus one juicy event turned out
to be enough structure for a soap opera that writes itself. Every spoken line is
generated; there is no scripted conversation underneath it.

## Making Turns Feel Connected

My first instinct for managing seven agents was simple round-robin turn-taking.
That felt flat. Everyone spoke, but the lines behaved like isolated monologues.
One villager would make an accusation and then the scheduler would move on to
somebody with no reason to answer it.

The useful change was mention bias. After each line, the engine looks for another
villager's name. If somebody was just named, that person has a high chance of
speaking next. Otherwise, the next speaker is chosen from the rest of the cast.

That small scheduling rule changed the texture of the output. An accusation can
produce a denial, then a jab that pulls an old relationship into the scene. The
model writes every response, while the harness lets conflict continue.

## Short Memory, Sharper Characters

Each agent sees only a rolling window of roughly the last eight feed lines.
That is intentional. Small models can lose the plot when too much context is
packed into every turn. A short window keeps the immediate situation clear and
leaves room for the persona, secret, and relationship instructions that define
the speaker.

The town therefore has a shared short-term memory rather than an enormous
transcript: enough to remember who just said what without sifting through the
entire history of Tinbury.

## Cleaning Up Small-Model Habits

The raw output also needed hygiene. Small models love to include `<think>` blocks,
wrap replies in quotation marks, prefix a line with `Name:`, or expand a single
response into narration and extra lines.

I added a cleaning pass between generation and the town feed. It removes closed
or dangling thinking blocks, keeps the first real line, strips wrapping quotes,
and removes a leading speaker-name prefix. The prompt still asks for one vivid,
short line, but the cleaner makes the UI resilient when the model ignores part
of that request.

## Getting the Town Offline on ZeroGPU

The live Space runs Qwen3-4B in-process with Transformers under `@spaces.GPU`.
There is no external inference API and nothing leaves the machine, which is the
core of the project's Off-the-Grid claim.

I did hit a real integration bug while wiring that path. The chat-template flow
gave me a tokenizer `BatchEncoding`, and my first attempt mishandled it by
expecting `.shape` in the wrong place. The fix was straightforward once the
boundary was clear: render the chat template to a string first, then tokenize
that string explicitly. The generated-token slice can then use the input tensor's
actual shape.

That experience reinforced a recurring lesson in model integration: make each
representation change explicit. Messages, prompt text, tokenized tensors, and
generated tokens are different things.

## Giving Seven Voices Seven Faces

I wanted the cast to feel like characters rather than rows in a chat log, so I
generated all seven portraits locally with FLUX.2 [klein], a 4B image model. The
full model did not fit on my 16GB development GPU. Quantizing it to 4-bit with
bitsandbytes made it fit and kept the portrait workflow offline.

Those portraits now appear in the roster and beside each villager's lines. The
art makes the town legible at a glance before you even read the speaker's name.

## Tracing Emergent Behavior

Emergence is fun to watch, but it can be difficult to debug from the final line
alone. Every beat now records a structured trace: the tick, speaker, role, model,
recent context shown to the model, full system prompt, cleaned output, and a UTC
timestamp.

The Gradio app exports the current session as JSONL in one click. That gives me a
concrete record for debugging character behavior and a direct path to sharing an
agent-trace dataset later.

I used OpenAI's Codex CLI to add this trace logging and its tests, and to assemble
the submission evidence pack. Those changes were committed with co-authorship
attribution so the development history records that collaboration clearly.

## What I Learned

At this scale, small models are more than enough for character improvisation.
The magic is not primarily in parameter count. It is in the harness: secrets
that create pressure, relationships that give reactions meaning, a short memory
that keeps the scene focused, and mention-biased turn-taking that lets conflict
continue.

A crowd of tiny minds is a genuinely different design space from one large
assistant. Smol Town only makes sense because the models are small enough to
imagine running a whole community of them.

Open the [live Space](https://huggingface.co/spaces/build-small-hackathon/smol-town),
drop an event into Tinbury, and stir the pot.
