import {Component, html} from "../lib/htm/preact.js";
import * as widgetAPI from "./widget-api.js";
import {SearchBox} from "./search-box.js";

const GIPHY_SEARCH_DEBOUNCE = 1000
let GIPHY_API_KEY = "HQku8974Uq5MZn3MZns46kXn2R4GDm75"
let GIPHY_MXC_PREFIX = "mxc://giphy.mau.dev/"

export function giphyIsEnabled() {
	return GIPHY_API_KEY !== ""
}

export function setGiphyAPIKey(apiKey, mxcPrefix) {
	GIPHY_API_KEY = apiKey
	if (mxcPrefix) {
		GIPHY_MXC_PREFIX = mxcPrefix
	}
}

export class GiphySearchTab extends Component {
	constructor(props) {
		super(props)
		this.state = {
			searchTerm: "",
			gifs: [],
			loading: false,
			error: null,
		}
		this.handleGifClick = this.handleGifClick.bind(this)
		this.searchKeyUp = this.searchKeyUp.bind(this)
		this.updateGifSearchQuery = this.updateGifSearchQuery.bind(this)
		this.searchTimeout = null
	}

	async makeGifSearchRequest() {
		try {
			const resp = await fetch(`https://api.giphy.com/v1/gifs/search?q=${this.state.searchTerm}&api_key=${GIPHY_API_KEY}`)
			// TODO handle error responses properly?
			const data = await resp.json()
			if (data.data.length === 0) {
				this.setState({gifs: [], error: "No results"})
			} else {
				this.setState({gifs: data.data, error: null})
			}
		} catch (error) {
			this.setState({error})
		}
	}

	componentWillUnmount() {
		clearTimeout(this.searchTimeout)
	}

	searchKeyUp(event) {
		if (event.key === "Enter") {
			clearTimeout(this.searchTimeout)
			this.makeGifSearchRequest()
		}
	}

	updateGifSearchQuery(event) {
		this.setState({searchTerm: event.target.value})
		clearTimeout(this.searchTimeout)
		this.searchTimeout = setTimeout(() => this.makeGifSearchRequest(), GIPHY_SEARCH_DEBOUNCE)
	}

	handleGifClick(gif) {
		widgetAPI.sendSticker({
			"body": gif.title,
			"info": {
				"h": gif.images.original.height,
				"w": gif.images.original.width,
				"size": gif.images.original.size,
				"mimetype": "image/webp",
			},
			"msgtype": "m.image",
			"url": GIPHY_MXC_PREFIX + gif.id,

			"id": gif.id,
			"filename": gif.id + ".webp",
		})
	}

	render() {
		// TODO display loading state?
		return html`
			<${SearchBox} onInput=${this.updateGifSearchQuery} onKeyUp=${this.searchKeyUp} value=${this.state.searchTerm} placeholder="Find GIFs"/>
			<div class="pack-list">
				<section class="stickerpack" id="pack-giphy">
					<div class="error">
						${this.state.error}
					</div>
					<div class="sticker-list">
						${this.state.gifs.map((gif) => html`
							<div class="sticker" onClick=${() => this.handleGifClick(gif)} data-gif-id=${gif.id}>
								<img src=${gif.images.fixed_height.url} alt=${gif.title} class="visible" data=/>
							</div>
						`)}
					</div>
					<div class="footer powered-by-giphy">
						<img src="./res/powered-by-giphy.png" alt="Powered by GIPHY"/>
					</div>
				</section>
			</div>
		`
	}
}
