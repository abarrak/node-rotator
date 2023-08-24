# Node Rotator

This repository contains the automated node rotator for managed kuberentes clusters.

<image src="https://raw.githubusercontent.com/abarrak/node-rotator/docs/1.png" width="80%" />

## Usage

Rotate the given cluster based on passed crietria.

```console
$ rotate [OPTIONS] [CLUSTER]
```

**Arguments**:

* `[CLUSTER]`: Name of the cluster (context) to run on. Default is current context.  [default: default]

**Options**:

* `--version`: Print the current CLI version.
* `--dry-run / --no-dry-run`: Run the procedure in dry mode (simulated).  [default: no-dry-run]
* `--provider [aws|oci|alibaba|self_managed|k3d]`: The targe cloud provider: oci, aws, alibaba, k3d.  [default: CloudProviders.self_managed]
* `--rotate-type [days]`: The rotation criteria type. Currently only 'days' supported  [default: RotationCriteria.days]
* `--rotate-value INTEGER`: The rotation value. Currently only for how long in 'days'.  [default: 60]
* `--provision-time INTEGER`: The wait window between provider provision calls in seconds. Default: 1 minute  [default: 60]
* `--oci-compartment-id TEXT`: OCI compartment id of the cluster. Provider specific.
* `--oci-cluster-id TEXT`: OCI cluster ocid. Provider specific.
* `--help`: Show this message and exit.

<image src="https://raw.githubusercontent.com/abarrak/node-rotator/docs/2.png" width="75%" />

## Development

Initialize the working space:

```bash
python3 -m venv ./
source ./bin/activate
pip3 install -r requirements.txt
```

Once done, deactivate the environment:

```bash
deactivate
```

## Roadmap

- [x] Support OCI.
- [ ] Enhance the self_managed clusters support.
- [ ] Add AWS provider.
- [ ] Add GCP provider.
- [ ] Add ABC provider.


## License

MIT.