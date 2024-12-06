#!/bin/bash

cd ../rula/modified-rula
cargo run --bin new_rula

cd ../rula
cargo run -- ../examples/v2/modified_swapping.rula ../examples/v2/config2.json

cd ../generated
cargo run --bin ruleset