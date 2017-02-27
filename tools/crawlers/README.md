## Crawlers
* newsCrawl
 * 1st gen news cralwer that specifically targets webpage structure and URL patterns - written by Josh
  * Writen in: Bash
  * Requres: wget, tor
  * Parsers are required per-site (not generic crawling)
  * TODO: SQL-backend instead of flat file, complete code refactoring
  * time* is called by a cron script. See UI/data/examples for more
