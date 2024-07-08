# Nextcloud News Filter

This library is designed to filter Feeds from [Nextcloud News](https://nextcloud.github.io/news/), by marking them as read.
It is originally based on [nextcloud-news-filter](https://github.com/mathisdt/nextcloud-news-filter) by mathisdt.

![PyPI - Version](https://img.shields.io/pypi/v/nextcloud_news_filter)
[![image](https://img.shields.io/pypi/pyversions/nextcloud_news_filter.svg)](https://pypi.python.org/pypi/nextcloud_news_filter)
![PyPI - License](https://img.shields.io/pypi/l/nextcloud_news_filter)

[![pipeline status](https://img.shields.io/gitlab/pipeline-status/lioman/nextcloud_news_filter?branch=main)](https://gitlab.com/lioman/nextcloud_news_filter/-/commits/main)
[![coverage report](https://img.shields.io/gitlab/pipeline-coverage/lioman/nextcloud_news_filter?branch=main)](https://gitlab.com/lioman/nextcloud_news_filter/-/commits/main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## State of this package

This package is in an early stage of development. Things like configuration may change heavily in this early stage.


## Usage

This can be used directly on the system via a cli or as serverless function

### Installation

#### CLI

If you want to use the CLI install it with `pipx install nextcloud_news_filter[cli]`

#### Scaleway Serverless function

A full documentation will follow. These are just the steps you need to follow.

- create a namespace
- add a function via UI
- Get the last Release file: nextcloud_news_filter-$TAG.zip
- upload this via UI or with `scw` cli
- add your credentials as variables/secrets
- create a cron trigger with your filter configuration

### Configuration

All settings concerning the nextcloud server is done via environment variables:

- NEXTCLOUD_URL - the url of your instance e.g 'https://nextcloud.example.com'
- NEXTCLOUD_USER - your username
- NEXTCLOUD_PASS - the password of your user

It is using Basic authentication, if you have enabled 2-factor-authentication it will probably not work

#### Filter

The json to configure your filters consists of two keys
`skipFeeds` to ignore Feeds from all filters.
and `filter` to actually filter feeds. These are the options:

- name: Name of the filter. **Mandatory**
- feedId: Id of the feed the filter should be limited to (if not there, the filter rule is applied to all feeds). **Optional**
- bodyRegex: Regex that is applied to search in body of the feed item. **Optional**
- titleRegex: Regex that is applied to search in the title of the feed entry. **Optional**
- hoursAge: Maximum lifetime of the feed entry.

**Example:**

```json
{
  "skipFeeds": [
    1678, 1683, 1681, 1682, 1684, 1680, 1659, 1654, 1658, 1657, 1656, 1660, 1655
  ],
  "filter": [
    {
      "name": "heise+",
      "feedId": 1592,
      "titleRegex": "heise\\+|heise\\-Angebot|TechStage"
    },
    {
      "name": "All with Advertisement in Body",
      "feedId": 1594,
      "bodyRegex": "^Advertisement: "
    },
    {
      "name": "Feed older then one day, for feed 1595",
      "feedId": 1595,
      "hoursAge": 24
    },
    {
      "name": "all > 20 Days all feeds (except for skipped ones)",
      "hoursAge": 480
    }
  ]
}
```
