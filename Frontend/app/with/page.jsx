'use client';
import React from "react";

const With = () => {
  const images = [
    "/with/spoid.png",
    "/with/dapanda.png",
    "/with/quick.png",
    "/with/placeholder.png",
    "/with/mylittle.png",
    // 필요한 만큼 사진 경로 추가
  ];

 
    return (
      <section>
      <div className="container mx-auto">
        <h2 className="section-title mb-8 xl:mb-16 text-center mx-auto">
          With Page
        </h2>
        <div className="flex flex-col items-start space-y-4">
          {images.map((src, index) => (
            <img key={index} src={src} alt={`Photo ${index + 1}`} className="w-40 h-40 object-contain" />
          ))}
        </div>
      </div>
    </section>
 
    );
  };

export default With;
