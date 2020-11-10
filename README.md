# Ionicons

## Build Icons

Build icons needs to be prefixed with `build-` to avoid conflicts with existing similar icons ex: `build-cart.svg`

* Add any new icons to the `src/` folder.
* Move any unused icons to the `svg/` folder.

## Updating Documentation

You can view the (theoretical latest cheatsheet for icons we support [here](http://buildcom.github.io/ionicons/cheatsheet.html))
The cheasheet is updated via master branch.

# More Info

The premium icon font for [Ionic Framework](http://ionicframework.com/). Designed by [@benjsperry](https://twitter.com/benjsperry).

Note: All brand icons are trademarks of their respective owners. The use of these trademarks does not indicate endorsement of the trademark holder by Drifty, nor vice versa.

Visit [ionicons.com](http://ionicons.com) and  check out the search feature, which has keywords identifying common icon names and styles. For example, if you search for “arrow” we call up every icon that could possibly be used as an arrow. We’ve also included each icon’s class name for easy copy/pasting when you’re developing!

We intend for this icon pack to be used with [Ionic](http://ionicframework.com/), but it’s by no means limited to it. Use them wherever you see fit, personal or commercial. They are free to use and licensed under [MIT](http://opensource.org/licenses/MIT).


## Build Instructions

This repo already comes with all the files built and ready to go, but can also build the fonts from the source.
It only requires Python 3 along with python package manager (pip3).

1) Using the system version of Python 3, use pip3 to install the following package:

    ```
    $ pip3 install svgutils
    ```

2) Add or subtract files from the `src/` folder you'd like to be apart of the font files.

3) Run the build command:

    ```
    $ python3 ./builder/generate.py
    ```

4) If you wish to verify the current cheatsheet with your latest changes, in the root of the repo folder run:

   ```
   $ python3 -m http.server 9000
   // open a browser and navigate to: http://localhost:9000/cheatsheet.html
   ```

## License

Ionicons is licensed under the [MIT license](http://opensource.org/licenses/MIT).
