// maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
// Copyright (C) 2020 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

const urlParams = new URLSearchParams(window.location.search);
const widgetId = urlParams.get('widgetId'); // if you know the widget ID, supply it.
console.log("Widget ID:"+widgetId);
const api = new mxwidgets.WidgetApi(widgetId, '*');


// Before doing anything else, request capabilities:
api.requestCapabilities(mxwidgets.StickerpickerCapabilities);
api.requestCapability(mxwidgets.MatrixCapabilities.MSC4039UploadFile);

api.on("ready", () => {console.log("ready event received")});

// Start the messaging
api.start();

// If waitForIframeLoad is false, tell the client that we're good to go
//api.sendContentLoaded();

export function sendSticker(content){
    const data = {
        content: {...content},
        name: content.body,
    };
    // do the same thing that tulir does
    delete data.content.id;
    // send data
    api.sendSticker(data);
}

/*
 *export function sendGIF(content){
 *    // just print out content, should be URL
 *    console.log("Content:"+content.url);
 *    return new Promise((resolve, reject) => {
 *    const xhr = new XMLHttpRequest();
 *    xhr.open('GET', content.url, true);
 *    xhr.onreadystatechange = function() {
 *      if (xhr.readyState === 4) {
 *        if (xhr.status === 200) {
 *          const responseData = xhr.responseText;
 *          // Call uploadFile with response data
 *          api.uploadFile(responseData)
 *            .then(result => {
 *                console.log("Here's the result:"+result.content_uri);
 *                // mess around with the content object, then send it as sticker
 *                content.url = result.content_uri;
 *                sendSticker(content);
 *              resolve(result);
 *            })
 *            .catch(error => {
 *              reject(error);
 *            });
 *        } else {
 *          reject(new Error('Failed to fetch data')); // Reject the outer promise if fetching data fails
 *        }
 *      }
 *    };
 *    xhr.send();
 *  }); 
 *}
 */

export async function sendGIF(content){
    // just print content, since it's a custom type with URL
    console.log("Content:"+content.url);
    // use fetch because I'm on IE
    const lol = await fetch(content.url);
    const uri_file = await lol.blob();
    // call uploadFile with this
    var result = await api.uploadFile(uri_file)
    console.log("Got URI:"+result.content_uri);
    content.url = result.content_uri;
    // get thumbnail
    //const thumb_uri = await fetch(content.info.thumbnail_url)
    //const thumb_file = await thumb_uri.blob();
    //result = await api.uploadFile(thumb_file)
    //console.log("Thumb URI:"+result.content_uri);
    //content.info.thumbnail_url = result.content_uri;
    // actually, just delete the thumbnail
    delete content.info.thumbnail_url;
    // finally, send it as sticker
    sendSticker(content);

}


/*
 *let widgetId = null
 *
 *window.onmessage = event => {
 *    if (!window.parent || !event.data) {
 *        return
 *    }
 *
 *    const request = event.data
 *    if (!request.requestId || !request.widgetId || !request.action || request.api !== "toWidget") {
 *        return
 *    }
 *
 *    if (widgetId) {
 *        if (widgetId !== request.widgetId) {
 *            return
 *        }
 *    } else {
 *        widgetId = request.widgetId
 *    }
 *
 *    let response
 *
 *    if (request.action === "visibility") {
 *        response = {}
 *    } else if (request.action === "capabilities") {
 *        response = { capabilities: ["m.sticker", "org.matrix.msc4039.upload_file"] }
 *    } else {
 *        response = { error: { message: "Action not supported" } }
 *    }
 *
 *    window.parent.postMessage({ ...request, response }, event.origin)
 *}
 *
 *export function sendSticker(content) {
 *    const data = {
 *        content: { ...content },
 *        // `name` is for Element Web (and also the spec)
 *        // Element Android uses content -> body as the name
 *        name: content.body,
 *    }
 *    // Custom field that stores the ID even for non-telegram stickers
 *    delete data.content.id
 *
 *    // This is for Element iOS
 *    const widgetData = {
 *        ...data,
 *        description: content.body,
 *        file: `${content.id}.png`,
 *    }
 *    // Element iOS explodes if there are extra fields present
 *    delete widgetData.content["net.maunium.telegram.sticker"]
 *
 *    window.parent.postMessage({
 *        api: "fromWidget",
 *        action: "m.sticker",
 *        requestId: `sticker-${Date.now()}`,
 *        widgetId,
 *        data,
 *        widgetData,
 *    }, "*")
 *}
 *
 *export function sendGIF(content) {
 *    const data = {
 *        content: { ...content },
 *        name: content.body,
 *        msgtype: "m.image"
 *    }
 *
 *    delete data.content.id
 *    // This is for Element iOS
 *    const widgetData = {
 *        ...data,
 *        description: content.body,
 *        file: `${content.id}.png`,
 *    }
 *
 *    window.parent.postMessage({
 *        api: "fromWidget",
 *        action: "m.room.message",
 *        requestId: `gif-${Date.now()}`,
 *        widgetId,
 *        data,
 *        widgetData,
 *    }, "*")
 *}
 */
