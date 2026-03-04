import React from "react";

function NotFound({ itemNumber }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-8">
      {/* Animated Icon */}
      <div className="relative mb-8">
        {/* Main box with search animation */}
        <div className="relative animate-bounce">
          <svg
            className="w-32 h-32 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
            />
          </svg>
        </div>

      </div>

      {/* Message */}
      <div className="text-center max-w-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-3">
          Product Not Found
        </h2>
        <p className="text-gray-600 mb-4">
          Sorry, we don't have the item <span className="font-semibold text-blue-600">{itemNumber}</span> in our inventory.
        </p>
        <p className="text-sm text-gray-500">
          This product may be discontinued, out of stock, or the item number might be incorrect.
          Please try searching with a different item number or contact support for assistance.
        </p>
      </div>
    </div>
  );
}

export default NotFound;