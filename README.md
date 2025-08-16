# VirtualAviationJapan VPM Distribution

## Install
(Recommend) If you have [vrc-get](https://github.com/anatawa12/vrc-get)

```vrc-get repo add https://vpm.virtualaviation.jp/vpm.json```

 If you have vpm cli,

```vpm add repo https://vpm.virtualaviation.jp/vpm.json```

or, if you have VRChat Creator Companion, [Click here](https://vpm.virtualaviation.jp/redirect).

## Packages
+ [UdonRadioCommunication-Redux](https://github.com/VirtualAviationJapan/UdonRadioCommunications-Redux)

## workflow
1. Create a pull request to add new package manifest into `/packages`
2. GitHub action updates VPM repository (`/VPM.json`) on PR branch
3. If the PR branch is merged, updated VPM repository is published to GitHub pages

## Local testing
Install [uv](https://github.com/astral-sh/uv) for dependency management

```bash
uv run main.py
```