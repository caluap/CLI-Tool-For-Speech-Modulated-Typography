# Description

This is a CLI tool to extract transcriptions, prosedic features, and generating captioned videos from media files.

# Create a conda environment

```bash
conda create -n <env-name>
```

to activate the environment run the following:

```bash
conda activate <env-name>
```

# Dependencies

- **If haven't yet installed Node JS version > 19**

  - check out `https://github.com/nodesource/distributions`
- **Node JS packages**:
  -----------------


  - Run the following command under the project root folder

  ```bash
  npm install
  ```
- **FFmpeg**: for audio extraction
  ----------------------------


  - **Sudo Install**
    ------------

    ```bash
    sudo apt install ffmpeg
    ```
  - **Non-sudo Install**
    ----------------

    ```bash
    git clone https://github.com/FFmpeg/FFmpeg/tree/master
    ```

    - Follow the `INSTALL.md` instruction
    - NOTE: if `make install` ran into permission error:
      Manually add the FFmpeg dir to `$PATH`
      ```bash
      ffmpeg=$PWD
      echo ffmpeg=$ffmpeg >> ~/.bashrc 
      echo export PATH=\$FFMPEG:\$PATH >> ~/.bashrc 
      source ~/.bashrc
      ```

      Verify that ffmpeg is added to path- `ffmpeg`
- **Python Package Libraries**
  -------------------

  ```bash
  pip3 install -r requirements.txt
  ```


# To Run

`node index.js`
