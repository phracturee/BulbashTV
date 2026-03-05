<?php

namespace App\Spider\Dto;

class SearchResultDto
{
    /** @var string */
    public $title;

    /** @var string|null */
    public $magnetLink;

    /** @var string|null */
    public $torrentUrl;

    /** @var string|null */
    public $infoUrl;

    /** @var string */
    public $spiderName;

    /**
     * SearchResultDto constructor.
     *
     * @param string      $title
     * @param string|null $magnetLink
     * @param string|null $torrentUrl
     * @param string|null $infoUrl
     * @param string      $spiderName
     */
    public function __construct(string $title, ?string $magnetLink, ?string $torrentUrl, ?string $infoUrl, string $spiderName)
    {
        $this->title = $title;
        $this->magnetLink = $magnetLink;
        $this->torrentUrl = $torrentUrl;
        $this->infoUrl = $infoUrl;
        $this->spiderName = $spiderName;
    }
}
