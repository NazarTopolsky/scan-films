Count how much times a phrase has been said on some show.

Uses data from [http://springfieldspringfield.co.uk/](http://springfieldspringfield.co.uk/)

Usage:

    python scan_film.py *series* *regex* *threads*

**series** - name of the series as it appears on springfieldspringfield

**regex** - regex to match

**threads** (optional) - number of threads to run downloading process (only works with concurrent.futures)

Example:

     python scan_film.py Archer phrasing

Output:

    "phrasing" was mentioned 40 time(s) in show "Archer" (93 episodes)

    0.43 times per episode

    Elapsed 7.4990 s, downloaded 4220106 bytes
