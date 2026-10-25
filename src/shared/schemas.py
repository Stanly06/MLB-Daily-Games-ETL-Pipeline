"""Spark schemas (DDL) used with `from_json` to parse the MLB Stats API payloads stored in Bronze.

Only the fields the platform uses are declared; `from_json` ignores the rest, so new fields
added by the API never break the pipeline. Validated against live responses (October 2026).
"""

_TEAM_REF = "struct<id:int,name:string>"
_PERSON_REF = "struct<id:int,fullName:string>"
_LINE_TEAM = "struct<runs:int,hits:int,errors:int,leftOnBase:int>"

SCHEDULE = f"""
struct<dates:array<struct<date:string,games:array<struct<
  gamePk:bigint, gameType:string, season:string, gameDate:string, officialDate:string,
  status:struct<abstractGameState:string,codedGameState:string,detailedState:string,reason:string>,
  teams:struct<
    home:struct<team:{_TEAM_REF},score:int,isWinner:boolean,leagueRecord:struct<wins:int,losses:int>,probablePitcher:{_PERSON_REF}>,
    away:struct<team:{_TEAM_REF},score:int,isWinner:boolean,leagueRecord:struct<wins:int,losses:int>,probablePitcher:{_PERSON_REF}>>,
  venue:struct<id:int,name:string>,
  decisions:struct<winner:{_PERSON_REF},loser:{_PERSON_REF},save:{_PERSON_REF}>,
  linescore:struct<currentInning:int,scheduledInnings:int,
    teams:struct<home:{_LINE_TEAM},away:{_LINE_TEAM}>>,
  dayNight:string, doubleHeader:string, gameNumber:int, isTie:boolean, description:string,
  seriesDescription:string, seriesGameNumber:int, gamesInSeries:int,
  rescheduledFrom:string, resumedFrom:string
>>>>>
"""

_BATTING = """struct<gamesPlayed:int,plateAppearances:int,atBats:int,runs:int,hits:int,doubles:int,
  triples:int,homeRuns:int,rbi:int,baseOnBalls:int,intentionalWalks:int,strikeOuts:int,hitByPitch:int,
  stolenBases:int,caughtStealing:int,sacFlies:int,sacBunts:int,totalBases:int,leftOnBase:int,
  groundIntoDoublePlay:int>"""

_PITCHING = """struct<gamesStarted:int,outs:int,inningsPitched:string,battersFaced:int,numberOfPitches:int,
  strikes:int,hits:int,runs:int,earnedRuns:int,baseOnBalls:int,intentionalWalks:int,strikeOuts:int,
  homeRuns:int,hitBatsmen:int,wildPitches:int,wins:int,losses:int,saves:int,saveOpportunities:int,
  holds:int,blownSaves:int,completeGames:int,shutouts:int,inheritedRunners:int,inheritedRunnersScored:int>"""

_PLAYER = f"""struct<person:{_PERSON_REF},jerseyNumber:string,
  position:struct<abbreviation:string,type:string>,battingOrder:string,
  stats:struct<batting:{_BATTING},pitching:{_PITCHING}>,
  gameStatus:struct<isSubstitute:boolean>>"""

_BOX_TEAM = f"""struct<team:{_TEAM_REF},
  teamStats:struct<fielding:struct<errors:int,assists:int,putOuts:int>>,
  players:map<string,{_PLAYER}>, pitchers:array<int>, batters:array<int>>"""

BOXSCORE = f"""
struct<teams:struct<home:{_BOX_TEAM},away:{_BOX_TEAM}>,
  info:array<struct<label:string,value:string>>,
  officials:array<struct<official:{_PERSON_REF},officialType:string>>>
"""

PEOPLE = """
struct<people:array<struct<id:int,fullName:string,firstName:string,lastName:string,primaryNumber:string,
  birthDate:string,birthCity:string,birthStateProvince:string,birthCountry:string,height:string,weight:int,
  active:boolean,currentTeam:struct<id:int>,
  primaryPosition:struct<code:string,name:string,type:string,abbreviation:string>,
  batSide:struct<code:string>,pitchHand:struct<code:string>,mlbDebutDate:string>>>
"""

TEAMS = """
struct<teams:array<struct<id:int,name:string,teamName:string,abbreviation:string,shortName:string,
  locationName:string,franchiseName:string,clubName:string,firstYearOfPlay:string,season:int,active:boolean,
  venue:struct<id:int,name:string>,league:struct<id:int,name:string>,division:struct<id:int,name:string>>>>
"""

VENUES = """
struct<venues:array<struct<id:int,name:string,active:boolean,
  location:struct<city:string,state:string,stateAbbrev:string,country:string,elevation:int,
    defaultCoordinates:struct<latitude:double,longitude:double>>>>>
"""

STANDINGS = """
struct<records:array<struct<league:struct<id:int>,division:struct<id:int>,
  teamRecords:array<struct<team:struct<id:int,name:string>,season:string,gamesPlayed:int,wins:int,losses:int,
    runsScored:int,runsAllowed:int,runDifferential:int,winningPercentage:string,divisionRank:string,
    leagueRank:string,gamesBack:string,wildCardGamesBack:string,clinchIndicator:string,
    streak:struct<streakCode:string>>>>>>
"""
