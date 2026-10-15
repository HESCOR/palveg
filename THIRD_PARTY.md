# Third-party assets and data

The browser dependencies in `assets/vendor/` were copied from the public PALVEG Shiny application to preserve its existing rendering and interface. They run locally; the deployed page does not depend on a CDN or Shiny service.

| Component | Version | Upstream licence |
| --- | --- | --- |
| Bootstrap | 3.4.1 | MIT |
| jQuery | 3.7.1 | MIT |
| ion.rangeSlider | 2.3.1 | MIT |
| selectize.js | 0.15.2 | Apache-2.0 |
| htmlwidgets | 1.6.4 | MIT |
| htmltools fill CSS | 0.5.9 | MIT |
| Leaflet | 1.3.1 | BSD-2-Clause |
| Proj4js | 2.6.2 | MIT |
| Proj4Leaflet | 1.0.1 | BSD-2-Clause |
| R leaflet binding and CSS | 2.2.3 | GPL-3.0 |
| Shiny CSS and selectize accessibility plugin | 1.14.0 | GPL-3.0 |
| strftime | 0.9.2 | MIT |

Licence texts are included under `assets/vendor/licenses/`, and original asset headers are retained. The original R leaflet sources are available at https://github.com/rstudio/leaflet/tree/v2.2.3; Shiny sources at https://github.com/rstudio/shiny; htmlwidgets at https://github.com/ramnathv/htmlwidgets/tree/v1.6.4; htmltools at https://github.com/rstudio/htmltools.

## Scientific output

Layer coordinates, colours, raster images, legends, and popup text are the public display outputs of https://oakern.shinyapps.io/palveg_v2/, exported on 15 October 2026. No ownership or new licence over those scientific outputs or the underlying model data is asserted by this port.

The application credits Kern, O.A., Dallmeyer, A., Maier, A., Schlüter, P., Vogel, A., and Vercauteren, N., *Forest or tundra? How different vegetation reconstructions of Last Glacial landscapes in Europe may shape our perception of early human dispersal processes* (in review). The [preprint](https://doi.org/10.31223/X5DR2G) links to the [data archive](https://doi.org/10.5281/zenodo.19630750), whose downloads were restricted at the time of this work. Those raw files are not included here.
