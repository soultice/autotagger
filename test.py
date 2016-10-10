import click


@click.command()
@click.option('--pos', type=str)
def test(pos):
    click.echo(pos)
