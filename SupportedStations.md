Maturity level:
  * High: Users are actively using it.
  * Medium: Reported to be working.
  * Low: Support has been recently implemented.

| **Vendor**| **Model** | **Link** | **Maturity** | **Auto-Detect** | **Driver** | **Notes** | **Linux** | **Windows** |
|:----------|:----------|:---------|:-------------|:----------------|:-----------|:----------|:----------|:------------|
| **Ambient Weather** | WS1080    | USB      | Medium       | No              | !wh1080    | See Fine Offset Electronics WH1080 | Yes       | ?           |
| **Davis** | VantagePro | Serial / USB? | High         | No              | !vantagepro2 |           | Yes       | ?           |
|           | VantagePro2 | Serial / USB? | High         | No              | !vantagepro2 |           | Yes       | ?           |
| **Elecsa**                  | AstroTouch 6975 | USB      | Medium       | No              | !wh1080    | See Fine Offset Electronics WH1080 | Yes       | ?           |
| **Fine Offset Electronics** | WH1080, WH1080PC | USB      | Medium       | No              | !wh1080    | Needs third party pywws library (http://code.google.com/p/pywws/downloads/list).<br>Install it as root with <code>setup.py</code>. <table><thead><th> Yes       </th><th> ?           </th></thead><tbody>
<tr><td>                         </td><td> WH1081    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                         </td><td> WH1090    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                         </td><td> WH1091    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                         </td><td> WH2080    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                         </td><td> WH2081    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>Freetec</b>                 </td><td> PX1117    </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>LaCrosse</b>                 </td><td> WS2300    </td><td> Serial   </td><td> Low          </td><td> No              </td><td> !ws2300    </td><td> Needs third party ws2300 library (<a href='http://ace-host.stuart.id.au/russell/files/ws2300/'>http://ace-host.stuart.id.au/russell/files/ws2300/</a>).<br />Run <code>sudo ./setup.py install</code> to make it visible to wfrog. </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                             </td><td> WS28xx, C86234 </td><td> USB      </td><td> Low          </td><td> Yes             </td><td> !ws28xx    </td><td> Needs third party ws28xx library (<a href='https://github.com/dpeddi/ws-28xx/'>https://github.com/dpeddi/ws-28xx/</a>)</td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>Oregon Scientific</b> </td><td> WMR100N   </td><td> USB      </td><td> High         </td><td> Yes?            </td><td> !wmrs200   </td><td>           </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                   </td><td> WMR88A    </td><td> USB      </td><td> High         </td><td> Yes?            </td><td> !wmrs200   </td><td> Seems to return always the same value for gust and avg wind (see <a href='https://code.google.com/p/wfrog/issues/detail?id=117'>issue 117</a>) </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                   </td><td> WMR200    </td><td> USB      </td><td> High         </td><td> Yes             </td><td> !wmr200    </td><td>           </td><td> Yes       </td><td> ?           </td></tr>
<tr><td>                   </td><td> WMRS200   </td><td> USB      </td><td> High         </td><td> Yes             </td><td> !wmrs200   </td><td>           </td><td> Yes       </td><td> Yes         </td></tr>
<tr><td>                   </td><td> WMR928NX  </td><td> Serial   </td><td> High         </td><td> No              </td><td> !wmr928x   </td><td>           </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>PCE</b>                  </td><td> FWS20     </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See Fine Offset Electronics WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>Scientific Sales</b>                  </td><td> Pro Touch Screen Weather Station </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See Fine Offset Electronics WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>TFA Dostmann</b> </td><td> Primus    </td><td> USB      </td><td> Low          </td><td> Yes             </td><td> !ws28xx    </td><td> See La Crosse ws28xx </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>Topcom National Geographic</b>        </td><td> 265NE     </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See Fine Offset Electronics WH1080 </td><td> Yes       </td><td> ?           </td></tr>
<tr><td> <b>Watson</b>                  </td><td> W8681     </td><td> USB      </td><td> Medium       </td><td> No              </td><td> !wh1080    </td><td> See Fine Offset Electronics WH1080 </td><td> Yes       </td><td> ?           </td></tr></tbody></table>

Note that some USB drivers in Linux need to be run as root.<br>
<p align='right'><img src='http://wfrog.googlecode.com/svn/wiki/images/small-frog.png' /></p>