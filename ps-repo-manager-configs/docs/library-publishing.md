# Publishing a Library


## Version

In order to publish a library we must be able to detect the current version of the library.
There is a single pipeline that handles versioning for all projects.
Detection of the version is done using multiple methods.

**Python** projects using **`poetry`** will extract the version from the `pyproject.toml` file.

**Javascript** and **Typescript** projects will have the version extracted from `package.json`.

**Java** extracts the version from `pom.xml`.

The simplest method for non-langauge geared projects is to echo the version from
a Makefile command like shown [here.](https://github.com/Pole-Star-Space-Applications-USA/ps-repo-manager-configs/blob/c67e574624e1b7341126107fe620faf021609e54/Makefile#L23)

When the pipeline detects a version has changed in a merge to `main/master` it will tag the current commit with that version and create a github "release".

## Publishing profiles

All the publishing actions are triggered by successful runs of the versioning pipeline (see [Version](#Version)).
When a new version is detected library publishing pipelines are triggered to release using the following commands:

### Javascript/Typescript
`npm publish` - use `prepublishOnly` script hook in `package.json` to build TS files (see [here](https://github.com/Pole-Star-Space-Applications-USA/ps-services-cdk/blob/9893443beedc37758210f32163055fc053c4b251/package.json#L24)).
