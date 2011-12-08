# secret-santa

A simple python script for doing a 'Secret Santa', where each of a bunch of 
people are given a secret Christmas gift by one of the others. 

Using the program should mean:

* No one needs to coordinate who is buying for whom 
* The person running the script won't even know the assignments (unless they 
  check their 'sent items')
* Santas are assigned pseudo-randomly

It's even possible to add 'exclusions' to avoid certain people from having to 
buy from each other, for example.

## Documentation

The basic invocation is something like:

      secret-santa.py email your-conf.conf

Where the `email` keyword argument says you want to send people their 
assignments via email, and the `your-conf.conf` is a configuration file
with the names of the participants in it. Other keyword arguments are
`print` and `email_check`.

A documented example configuration file (`example.conf`) is provided.

The program also responds to `secret-santa.py --help`

## License

See the `LICENSE` file
