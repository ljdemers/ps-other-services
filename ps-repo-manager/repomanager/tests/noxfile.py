import nox


@nox.session(python=["3.6", "3.8", "3.10"])
def tests(session):

    session.run("python", "--version")

    session.run(
        "poetry",
        "update",
    )  # Do this to get most current libraries instead of the locked libs
    session.run("poetry", "install")

    session.run("pytest")
