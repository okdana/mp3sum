# mp3sum

## What is it?

`mp3sum` is a utility for verifying the integrity of MP3 files. You can think of
it like an
[SFV checker](https://en.wikipedia.org/wiki/Simple_file_verification), except
that it still works even after you've re-tagged the MP3.

![mp3sum screen shot](https://raw.githubusercontent.com/okdana/mp3sum/master/screenshot.png)

## How does it work?

When the [LAME](http://lame.sourceforge.net/) encoder creates an MP3 file, it
embeds a [CRC-16](https://en.wikipedia.org/wiki/Cyclic_redundancy_check) check
sum of the file's audio stream in the file's header. Since only the audio stream
is used to compute the check sum, it is not affected by meta-data modifications
(such as changing tags, adding lyrics, and applying cover art) that occur after
the file has been created. This means that, no matter how much the file's tags
are changed afterwards, the check sum still applies. Re-computing the check sum
and comparing it to the one embedded in the file allows `mp3sum` to verify that
the data in the file has not been corrupted.

## How do i use it?

First, install the utility:

```
% git clone git@github.com:okdana/mp3sum.git
% cd mp3sum
% sudo pip3 install -r requirements.txt
% sudo make install
```

(If you don't have Python 3, use `pip` instead of `pip3` for the third step.)

Then, simply pass `mp3sum` any MP3s (or directories of MP3s) you wish to verify,
as shown in the screen shot above.

## What does the output mean?

`mp3sum` prints file results one per line in a format like the following:

```
P D4CB:D4CB C6FD:C6FD 01  -  Scissor Runner.mp3
```

* `P` is the result code. This may be `P` for *pass*, `U` for *unsupported*, or
  `F` for *fail*. This code is provided primarily for easy batch scripting.

* `D4CB:D4CB` is the computed and expected info tag CRC (respectively). The tag
  CRC must be valid before `mp3sum` will go on to check the audio stream. If the
  tag CRC is missing or uncomputable, it will be printed as all zeroes.

* `C6FD:C6FD` is the computed and expected music CRC (respectively). The music
  CRC represents the actual audio data in the file. If the music CRC is missing
  or uncomputable, it will be printed as all zeroes.

* `01  -  Scissor Runner.mp3` is the path or name of the MP3 file.

## What are pass, unsupported, and fail?

File checks may return one of three results:

* **Pass** — `mp3sum` was able to compute both the tag CRC and the music CRC and
  confirm that they match what was embedded in the file. This result indicates a
  good (non-corrupt) MP3 file.

* **Unsupported** — `mp3sum` can only verify the integrity of MP3s created by
  the LAME encoder, version 3.90 or later. If the file was created with another
  encoder (such as the one built into iTunes), or with an old version of LAME,
  or if there's any reason that the CRC could not be found or computed, an
  unsupported result will be returned. There's not necessarily anything wrong
  with an unsupported file — but, unless you have a valid SFV, you'll never
  really know.

* **Fail** — Either the computed tag CRC or the computed music CRC didn't match
  the original value embedded in the file. This usually means that the file is
  corrupt, though there are non-corruption-related reasons that the info tag or
  audio stream might have been modified (see below).

## What does a failed check mean?

Normally, a failed check means that the file is corrupt. This is especially
likely if only one or two of the files in an album fails. Another reason only
some of the files might fail is if the album was pieced together from multiple
rips.

If *all* files in an album fail, it's more likely that there is some other,
non-corruption-related, explanation. The three most common reasons are:

* A scene group has modified the info tag, probably to change the encoder
  version string, rendering the info tag CRC invalid.

* Someone has applied destructive volume normalisation (cf.
  [MP3Gain](http://mp3gain.sourceforge.net/)) to the audio stream, rendering the
  music CRC invalid.

* `mp3sum` simply doesn't know how to read the file, because its developer is
  stupid.

## Why are the files out of order?

`mp3sum` is multi-threaded to improve check speed. Since checks are performed in
parallel, it is likely that at least a few of the files will be out of order in
the output. If this is bothersome for some reason, supplying `--workers 1` will
put the files back in order (at the cost of longer check times).

## What's the licence?

As usual, `mp3sum` is provided under the MIT licence.

## Where can i learn more?

* http://gabriel.mp3-tech.org/mp3infotag.html

