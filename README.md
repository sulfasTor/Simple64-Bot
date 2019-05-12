

# Stratégie principale

La stratégie consiste à créer un armée suffisamment grande pour
pouvoir lancer une attaque finale contre l'ennemi.

Pour cela nous suivons des taux de construction des bâtiments.


## Taux des unités

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-right" />

<col  class="org-right" />

<col  class="org-right" />

<col  class="org-left" />

<col  class="org-right" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">Etape</th>
<th scope="col" class="org-right">SCV</th>
<th scope="col" class="org-right">Supply depot (sp)</th>
<th scope="col" class="org-right">Barrack (br)</th>
<th scope="col" class="org-left">Refinery (r)</th>
<th scope="col" class="org-right">Marine (m)</th>
</tr>
</thead>

<tbody>
<tr>
<td class="org-left">Début</td>
<td class="org-right">15</td>
<td class="org-right">5</td>
<td class="org-right">1</td>
<td class="org-left">1</td>
<td class="org-right">15</td>
</tr>


<tr>
<td class="org-left">1er incrément</td>
<td class="org-right">21</td>
<td class="org-right">6</td>
<td class="org-right">2</td>
<td class="org-left">-</td>
<td class="org-right">22</td>
</tr>


<tr>
<td class="org-left">2ème incrément</td>
<td class="org-right">27</td>
<td class="org-right">7</td>
<td class="org-right">3</td>
<td class="org-left">-</td>
<td class="org-right">29</td>
</tr>


<tr>
<td class="org-left">3ème incrément</td>
<td class="org-right">23</td>
<td class="org-right">8</td>
<td class="org-right">4</td>
<td class="org-left">-</td>
<td class="org-right">36</td>
</tr>


<tr>
<td class="org-left">4èeme incrément</td>
<td class="org-right">-</td>
<td class="org-right">-</td>
<td class="org-right">-</td>
<td class="org-left">-</td>
<td class="org-right">43</td>
</tr>


<tr>
<td class="org-left">Dernier</td>
<td class="org-right">-</td>
<td class="org-right">-</td>
<td class="org-right">-</td>
<td class="org-left">-</td>
<td class="org-right">60</td>
</tr>
</tbody>
</table>


# Stratégie de construction

Pour construire des bâtiments nous avons la logique suivante:

1.  Sélectionner l'unité ou bâtiment correspondante aléatoirement.
2.  Construire le premier bâtiment ou unité avec des coordonnées fixes
    d'accord à l'endroit d'apparition.
3.  Vérifier si le bâtiment est construit.
4.  Sinon réessayer.
5.  Si oui répeter pendant que le taux n'est pas atteint.
6.  Générer des coordonnés aléatoires proches des bâtiments pour la suite.


# Stratégie d'attaque

Lorsque nous atteignons le taux final de Marines, nous lançons une
attaque.
Nous observons si un ennemi est à la porte et si oui nous
sélectionnons toutes les unités et l'attaquont. Sinon nous ne
rapprochons du centre ou génerons une coordonnée aléatoire si on
dépasse les bornes de la carte.


# Résultats


## Difficulté Easy (10 parties)

Taux de réussite de 90% dont 30% victoire, 60% nul, 10% défaite.


## Difficulté Médium (10 parties)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-right" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-right">steps</th>
<th scope="col" class="org-left">outcome</th>
<th scope="col" class="org-left">reward</th>
<th scope="col" class="org-left">score</th>
</tr>
</thead>

<tbody>
<tr>
<td class="org-right">14184</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[3455]</td>
</tr>


<tr>
<td class="org-right">21320</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[3542]</td>
</tr>


<tr>
<td class="org-right">19248</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[1332]</td>
</tr>


<tr>
<td class="org-right">20200</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[4309]</td>
</tr>


<tr>
<td class="org-right">14456</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[3916]</td>
</tr>


<tr>
<td class="org-right">12080</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[4178]</td>
</tr>


<tr>
<td class="org-right">25000</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[2335]</td>
</tr>


<tr>
<td class="org-right">21720</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[4080]</td>
</tr>


<tr>
<td class="org-right">18152</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[3738]</td>
</tr>


<tr>
<td class="org-right">19288</td>
<td class="org-left">[-1]</td>
<td class="org-left">[-1]</td>
<td class="org-left">[4137]</td>
</tr>
</tbody>
</table>

