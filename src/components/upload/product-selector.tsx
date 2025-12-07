"use client";

import { useState } from "react";
import { Search, Package, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ProductPlacement } from "@/types";

// Sample products - in a real app, this would come from an API
const SAMPLE_PRODUCTS: ProductPlacement[] = [
  {
    id: "1",
    name: "iPhone 15 Pro",
    description: "Latest flagship smartphone with titanium design",
    category: "Technology"
  },
  {
    id: "2",
    name: "Nike Air Max",
    description: "Classic athletic sneakers with air cushioning",
    category: "Fashion"
  },
  {
    id: "3",
    name: "Coca-Cola Classic",
    description: "Iconic red can soft drink beverage",
    category: "Food & Beverage"
  },
  {
    id: "4",
    name: "Tesla Model 3",
    description: "Electric sedan with autopilot capabilities",
    category: "Automotive"
  },
  {
    id: "5",
    name: "MacBook Pro",
    description: "Professional laptop with M3 chip",
    category: "Technology"
  },
  {
    id: "6",
    name: "Starbucks Coffee Cup",
    description: "Branded disposable coffee cup with logo",
    category: "Food & Beverage"
  }
];

interface ProductSelectorProps {
  selectedProduct: ProductPlacement | null;
  onProductSelect: (product: ProductPlacement | null) => void;
}

export function ProductSelector({ selectedProduct, onProductSelect }: ProductSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customProduct, setCustomProduct] = useState({
    name: "",
    description: "",
    category: ""
  });

  const filteredProducts = SAMPLE_PRODUCTS.filter(product =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = Array.from(new Set(SAMPLE_PRODUCTS.map(p => p.category)));

  const createCustomProduct = () => {
    if (customProduct.name && customProduct.description && customProduct.category) {
      const newProduct: ProductPlacement = {
        id: `custom-${Date.now()}`,
        ...customProduct
      };
      onProductSelect(newProduct);
      setCustomProduct({ name: "", description: "", category: "" });
      setShowCustomForm(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Select Product for Placement</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCustomForm(!showCustomForm)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Custom Product
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Custom Product Form */}
        {showCustomForm && (
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <h4 className="font-medium text-gray-900">Create Custom Product</h4>
            <div className="grid grid-cols-1 gap-3">
              <Input
                placeholder="Product name..."
                value={customProduct.name}
                onChange={(e) => setCustomProduct(prev => ({ ...prev, name: e.target.value }))}
              />
              <Input
                placeholder="Product description..."
                value={customProduct.description}
                onChange={(e) => setCustomProduct(prev => ({ ...prev, description: e.target.value }))}
              />
              <Input
                placeholder="Category..."
                value={customProduct.category}
                onChange={(e) => setCustomProduct(prev => ({ ...prev, category: e.target.value }))}
              />
              <div className="flex space-x-2">
                <Button
                  onClick={createCustomProduct}
                  disabled={!customProduct.name || !customProduct.description || !customProduct.category}
                  size="sm"
                >
                  Create Product
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCustomForm(false)}
                  size="sm"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <Badge key={category} variant="outline">
              {category}
            </Badge>
          ))}
        </div>

        {/* Selected Product */}
        {selectedProduct && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Package className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium text-blue-900">{selectedProduct.name}</h4>
                  <p className="text-sm text-blue-700">{selectedProduct.description}</p>
                  <Badge variant="outline" className="mt-2">
                    {selectedProduct.category}
                  </Badge>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onProductSelect(null)}
                className="text-blue-600 hover:text-blue-800"
              >
                Change
              </Button>
            </div>
          </div>
        )}

        {/* Product List */}
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {filteredProducts.map((product) => (
            <div
              key={product.id}
              className={`p-3 border border-gray-200 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${
                selectedProduct?.id === product.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
              }`}
              onClick={() => onProductSelect(product)}
            >
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Package className="w-4 h-4 text-gray-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900">{product.name}</h4>
                  <p className="text-xs text-gray-500 mt-1">{product.description}</p>
                  <Badge variant="outline" className="mt-2 text-xs">
                    {product.category}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredProducts.length === 0 && searchQuery && (
          <div className="text-center py-8 text-gray-500">
            <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p>No products found matching "{searchQuery}"</p>
            <p className="text-sm">Try creating a custom product instead</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}