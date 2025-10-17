<div align="center" markdown>
<img src="!PLACEHOLDER!"/>

# Update repos as a ninja

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/!PLACEHOLDER!)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/!PLACEHOLDER!)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/!PLACEHOLDER!)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/!PLACEHOLDER!)](https://supervise.ly)

</div>

## Overview

This app allows you to easily run scripts from the Ninja repository provided in the JSON file list of repositories.

## Preparation

1. First, you need to obtain and register the GitHub SSH key as described in [this article](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).
2. Put the private key (usually `id_rsa`) in the TeamFiles folder.
3. Now you can launch the app from the private key file.

## How To Run

1. Launch the app from the context menu of your ssh key file (`id_rsa`) in the TeamFiles folder.
2. Select repositories to update in the Transfer widget in Step 2️⃣.
3. Config forces in Step 3️⃣ (optional).
4. Press the `Start` button.
