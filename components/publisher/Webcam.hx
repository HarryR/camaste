/* ************************************************************************ */
/*                                                                          */
/*  haXe Video                                                              */
/*  Copyright (c)2007 Nicolas Cannasse                                      */
/*  Copyright (c)2011 af83                                                  */
/*                                                                          */
/* This library is free software; you can redistribute it and/or            */
/* modify it under the terms of the GNU Lesser General Public               */
/* License as published by the Free Software Foundation; either             */
/* version 2.1 of the License, or (at your option) any later version.       */
/*                                                                          */
/* This library is distributed in the hope that it will be useful,          */
/* but WITHOUT ANY WARRANTY; without even the implied warranty of           */
/* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU        */
/* Lesser General Public License or the LICENSE file for more details.      */
/*                                                                          */
/* ************************************************************************ */
class Webcam {
    var nc : flash.net.NetConnection;
    var ns : flash.net.NetStream;
    var cam : flash.media.Camera;
    var mic : flash.media.Microphone;
    var file : String;
    var share : String;

    public function new(host, file,?share, token, width, height, fps) {
        this.file = file;
        this.share = share;
        this.cam = flash.media.Camera.getCamera();
        if( this.cam == null )
            throw "Webcam not found";
        this.cam.setMode(width, height, fps, true);
        this.mic = flash.media.Microphone.getMicrophone();
        this.nc = new flash.net.NetConnection();
        this.nc.addEventListener(flash.events.NetStatusEvent.NET_STATUS,onEvent);
        this.nc.connect(host, token);
    }

    public function getCam() {
        return this.cam;
    }

    function onEvent(e) {
        if( e.info.code == "NetConnection.Connect.Success" ) {
            this.ns = new flash.net.NetStream(nc);
            this.ns.addEventListener(flash.events.NetStatusEvent.NET_STATUS, onEvent);


            this.cam.setQuality(50 * 1024, 0);		// 16 kilobytes per second
            this.cam.setMode(320, 240, 30, true);	// 320x240, 30fps
            this.cam.setKeyFrameInterval(15);		// Keyframes twice a second

            var h264settings = new flash.media.H264VideoStreamSettings();
            h264settings.setProfileLevel( flash.media.H264Profile.BASELINE, flash.media.H264Level.LEVEL_3_1 );
	    this.ns.videoStreamSettings = h264settings;
            this.ns.publish(this.file,this.share);

	    var metaData:Dynamic = {};
	    metaData.codec = ns.videoStreamSettings.codec;
            metaData.profile = h264settings.profile;
            metaData.level = h264settings.level;
            metaData.fps = this.cam.fps;
            metaData.bandwidth = this.cam.bandwidth;
            metaData.width = this.cam.width;
            metaData.height = this.cam.height;
            metaData.keyFrameInterval = this.cam.keyFrameInterval;
            this.ns.send("@setDataFrame", "onMetaData", metaData);
        }
	else if (e.info.code == "NetStream.Publish.Start") {
            this.ns.attachCamera(this.cam);
            this.ns.attachAudio(this.mic);
            this.ns.bufferTime = 0.5;
        }
    }

    public function doStop() {
        if( this.ns != null )
            this.ns.close();
        this.nc.close();
    }
}
