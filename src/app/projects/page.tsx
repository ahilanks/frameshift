"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Video,
  Search,
  Filter,
  Download,
  Eye,
  MoreVertical,
  Calendar,
  Tag,
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDuration } from "@/lib/utils";

// Mock project data
const MOCK_PROJECTS = [
  {
    id: "1",
    name: "Urban Lifestyle Video",
    product: "iPhone 15 Pro",
    category: "Technology",
    createdAt: "2024-12-05T10:30:00Z",
    duration: 15.5,
    status: "completed",
    thumbnail: "/placeholder-thumbnail.jpg",
    metrics: {
      visibilityPercentage: 23.3,
      exposureDuration: 3.5
    }
  },
  {
    id: "2",
    name: "Coffee Shop Scene",
    product: "Starbucks Coffee Cup",
    category: "Food & Beverage",
    createdAt: "2024-12-04T14:20:00Z",
    duration: 8.2,
    status: "completed",
    thumbnail: "/placeholder-thumbnail.jpg",
    metrics: {
      visibilityPercentage: 18.7,
      exposureDuration: 2.1
    }
  },
  {
    id: "3",
    name: "Athletic Performance",
    product: "Nike Air Max",
    category: "Fashion",
    createdAt: "2024-12-03T09:15:00Z",
    duration: 22.8,
    status: "completed",
    thumbnail: "/placeholder-thumbnail.jpg",
    metrics: {
      visibilityPercentage: 31.2,
      exposureDuration: 4.8
    }
  },
  {
    id: "4",
    name: "Tech Review Demo",
    product: "MacBook Pro",
    category: "Technology",
    createdAt: "2024-12-02T16:45:00Z",
    duration: 45.3,
    status: "processing",
    thumbnail: "/placeholder-thumbnail.jpg",
    metrics: {
      visibilityPercentage: 0,
      exposureDuration: 0
    }
  }
];

const CATEGORIES = ["All", "Technology", "Fashion", "Food & Beverage", "Automotive"];

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortBy, setSortBy] = useState("newest");

  const filteredProjects = MOCK_PROJECTS.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         project.product.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || project.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  const sortedProjects = [...filteredProjects].sort((a, b) => {
    switch (sortBy) {
      case "newest":
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      case "oldest":
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      case "name":
        return a.name.localeCompare(b.name);
      default:
        return 0;
    }
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Projects</h1>
            <p className="text-gray-600 mt-1">
              Manage and view your AI-enhanced videos
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Link href="/">
              <Button>
                <Video className="w-4 h-4 mr-2" />
                New Project
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Category Filter */}
            <div className="flex gap-2">
              {CATEGORIES.map((category) => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="name">Name A-Z</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Projects Grid */}
      {sortedProjects.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Video className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
              <p className="text-gray-500 mb-6">
                {searchQuery || selectedCategory !== "All"
                  ? "Try adjusting your search or filters"
                  : "Get started by creating your first AI-enhanced video"
                }
              </p>
              <Link href="/">
                <Button>
                  <Video className="w-4 h-4 mr-2" />
                  Create New Project
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedProjects.map((project) => (
            <Card key={project.id} className="group hover:shadow-lg transition-shadow cursor-pointer">
              <div className="relative">
                {/* Thumbnail */}
                <div className="aspect-video bg-gray-200 rounded-t-lg relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <Video className="w-12 h-12 text-white opacity-70" />
                  </div>
                  <div className="absolute top-3 left-3">
                    <Badge
                      variant={project.status === "completed" ? "default" : "secondary"}
                      className={project.status === "completed" ? "bg-green-100 text-green-800" : ""}
                    >
                      {project.status === "completed" ? "Complete" : "Processing"}
                    </Badge>
                  </div>
                  <div className="absolute bottom-3 right-3">
                    <Badge variant="secondary" className="text-xs">
                      {formatDuration(project.duration)}
                    </Badge>
                  </div>
                </div>

                {/* Content */}
                <CardContent className="p-4">
                  <div className="space-y-3">
                    {/* Title and Product */}
                    <div>
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                        {project.name}
                      </h3>
                      <div className="flex items-center mt-1 text-sm text-gray-500">
                        <Tag className="w-3 h-3 mr-1" />
                        {project.product}
                      </div>
                    </div>

                    {/* Metrics */}
                    {project.status === "completed" && (
                      <div className="flex justify-between text-xs text-gray-500">
                        <div className="flex items-center">
                          <Eye className="w-3 h-3 mr-1" />
                          {project.metrics.visibilityPercentage.toFixed(1)}% visible
                        </div>
                        <div className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {project.metrics.exposureDuration.toFixed(1)}s exposure
                        </div>
                      </div>
                    )}

                    {/* Date and Category */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-xs text-gray-400">
                        <Calendar className="w-3 h-3 mr-1" />
                        {formatDate(project.createdAt)}
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {project.category}
                      </Badge>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-2">
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Eye className="w-3 h-3 mr-1" />
                          View
                        </Button>
                        {project.status === "completed" && (
                          <Button size="sm" variant="outline">
                            <Download className="w-3 h-3 mr-1" />
                            Download
                          </Button>
                        )}
                      </div>
                      <Button size="icon" variant="ghost" className="w-6 h-6">
                        <MoreVertical className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Stats Summary */}
      {sortedProjects.length > 0 && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Project Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {MOCK_PROJECTS.length}
                </div>
                <div className="text-sm text-gray-500">Total Projects</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {MOCK_PROJECTS.filter(p => p.status === "completed").length}
                </div>
                <div className="text-sm text-gray-500">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {MOCK_PROJECTS.filter(p => p.status === "processing").length}
                </div>
                <div className="text-sm text-gray-500">Processing</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {new Set(MOCK_PROJECTS.map(p => p.category)).size}
                </div>
                <div className="text-sm text-gray-500">Categories</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}